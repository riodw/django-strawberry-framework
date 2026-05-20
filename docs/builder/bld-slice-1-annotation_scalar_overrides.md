# Build: Slice 1 — Track annotation-only scalar overrides on DjangoTypeDefinition

Spec reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md` (lines 85-118; the Slice 1 sub-checklist starts at line 85 and the last Relay-collision sub-bullet ends at line 118)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `consumer_annotated_relation_fields` collection at `django_strawberry_framework/types/base.py:95-97` is the direct template — the new `consumer_annotated_scalar_fields` collection walks the same `consumer_annotations = dict(getattr(cls, "__annotations__", {}))` dict (line 94) and the same `fields` tuple; only the `field.is_relation` polarity flips to `not field.is_relation`. Two-line parallel shape, zero new helpers.
  - `consumer_authored_fields` frozenset union at `types/base.py:119-125` already accepts splat-merged set members; one additional `*consumer_annotated_scalar_fields` line slots in alongside the existing three.
  - `DjangoTypeDefinition` dataclass field-defaults pattern at `types/definition.py:28-31` (`consumer_*_fields: frozenset[str] = frozenset()`) is reused verbatim for the new field; immutable default, no `field(default_factory=...)` needed.
  - `_build_annotations`'s scalar branch already short-circuits on `consumer_authored_fields` membership at `types/base.py:751-757`. Once the new collection lands in the union, the existing short-circuit fires for annotation-only scalars with no body edit.
  - The Relay-collision guard reuses the existing relay-shaped detection idiom from `_build_annotations:716` — `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` — applied verbatim inside `__init_subclass__`. Identical predicate at both sites is fine: the guard fires once at class-creation time and `_build_annotations`'s own check stays the per-field gating mechanism.
  - `StrawberryField` is already imported at `types/base.py:33`; `ConfigurationError` at `:35`; `relay` at `:32`. No new dependency-direction concerns.
  - Test infrastructure on the new tests reuses three existing fixtures: the `_isolate_registry` autouse fixture at `tests/types/test_definition_order.py:13-18` (registry clear between tests); the `_strawberry_field` helper at `:21-30` (resolves a named Strawberry field by python_name); and the `_introspect_field_type` helper at `tests/types/test_converters.py:434-446` (introspection through `NON_NULL` for end-to-end assertions). `_FakeArrayField` at `tests/types/test_converters.py:449-466` and the `_ARRAY_FIELD_CLS` monkeypatch idiom are reused verbatim for the nested-`ArrayField` bypass test.

- **New helpers justified.**
  - `_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")` — module-scope compiled-once regex above `DjangoType`. Single responsibility: token-shaped NodeID-string match for the fail-soft branch of `_id_annotation_is_relay_node_id`. Justified because (a) it must compile once per process, (b) it is used inside the helper's `except` branch where local-scope `re.compile` would re-compile on every fail-soft trip, and (c) the regex shape is the precise contract that distinguishes the rev7 H1 tightening (`(?:^|\.)NodeID\[`) from the rev6 plain-substring check (`"NodeID[" in raw`) — pinning it as a named module constant makes the contract reviewable.
  - `_has_node_id_marker(hint: object) -> bool` — module-scope helper. Single responsibility: detect that `hint` is `Annotated[T, NodeIDPrivate()]` (which `relay.NodeID[T]` reduces to in installed Strawberry). Used by both the success path of `_id_annotation_is_relay_node_id` AND the fail-soft sub-case-2 fallback (rev6 H1: when `id` is already resolved but a sibling annotation tripped `NameError`). Two call sites are the load-bearing justification.
  - `_id_annotation_is_relay_node_id(cls: type) -> bool` — module-scope helper. Single responsibility: detect that `cls.__annotations__["id"]` resolves to a NodeID marker, with rev5/rev6/rev7 fail-soft scoping for unresolved forward references. Called once from the H1 guard inside `__init_subclass__`. Justified as a separate function because the try/except + fail-soft sub-case logic would be 15+ lines inline; extracted, the guard body stays readable and the helper is unit-testable through the Slice 1 Relay-collision cluster.
  - Per spec Decision 7 the three helpers live in `types/base.py` (the same module as the guard call site). No new sibling module is justified — three short helpers in the file that already owns `__init_subclass__` keeps the call graph local.

- **Duplication risk avoided.**
  - The naive shape would have inlined the relay-shaped predicate `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` only at the guard call site without a follow-up note, leaving the existing `_build_annotations:716` site as a parallel near-copy with no cross-reference. Plan: implement the guard with the same expression verbatim and DO NOT extract a new `_is_relay_shaped(cls, interfaces)` helper for this slice — extracting an unused-third-call-site helper is premature, and the two existing call sites have legitimately different timing (class-creation vs. annotation synthesis). Worker 1 makes a follow-up note for the integration pass to revisit whether a shared helper is justified after Slice 1 ships.
  - The naive shape would have written four parametrized assertions for the relay-shaped detection across `Meta.interfaces` and direct subclass paths. Plan: write the two reject paths as separate tests (`test_consumer_id_annotation_on_relay_node_type_raises` for `Meta.interfaces` form, `test_consumer_id_annotation_on_direct_relay_node_subclass_raises` for direct subclass form per rev8 H1) without parametrization — the test names document the predicate halves the spec explicitly calls out, and parametrization would dilute the per-test focus. The spec's rev8 H1 entry explicitly permits Worker 1 to parametrize but does not require it; planning chooses the clearer name-per-shape form.
  - The TODO anchors in `types/base.py:98-114` (Decision 1 collection), `:126-207` (Decision 7 guard), `types/definition.py:30-41` (new field placement), `tests/types/test_definition_order.py:312-428` (Slice 1 cluster), `tests/types/test_converters.py:1040-1071` (ArrayField bypass), and `tests/types/test_base.py:454-462` (Slice 2 delete; not touched in this slice) are pre-written pseudocode that Worker 2 transcribes mechanically — Worker 2 must not invent a parallel structure, must not "improve" the regex shape, and must not re-order the fail-soft sub-cases. The DRY risk is "thinking it through twice" — Worker 1 already thought it through during spec authoring.
  - The four `consumer_*_fields` sets are independent input channels (per spec Decision 6); the plan keeps them as four separate frozensets on `DjangoTypeDefinition` (not collapsed into a tagged-union dict). Worker 2 must not collapse them — the introspection surface is the contract.

### Implementation steps

Note: line numbers below are pin-at-write-time hints from the current `main` HEAD. Worker 2 verifies against the working source before editing. Slice 1 is one commit; ordering matters because some steps reference symbols introduced by earlier steps.

1. **`django_strawberry_framework/types/base.py:28-33` — Add four module-level imports.** Insert `import re` and `import typing` in the standard-library group (currently `from collections.abc import Mapping, Sequence` at `:28` and `from typing import Any, ClassVar` at `:29`); add `Annotated` to the existing `from typing import` line at `:29` (becoming `from typing import Annotated, Any, ClassVar`); add `from strawberry.relay.types import NodeIDPrivate` next to the existing `from strawberry.types.field import StrawberryField` at `:33`. Rationale: the three module-scope helpers need `re`, `typing`, `Annotated`, and `NodeIDPrivate`; consolidating into the existing import groups keeps lint clean (Ruff isort sorts these into place automatically — Worker 2 may add them anywhere in their respective groups and `ruff check --fix` will sort).

2. **`django_strawberry_framework/types/base.py` — Add three module-scope helpers above `class DjangoType` (currently at `:69`).** Insert immediately before the `class DjangoType:` line (after the `ALLOWED_META_KEYS` block at `:55-66`). The bodies are verbatim from spec Decision 7's pseudocode block at `spec:541-657`; transcribe them exactly:

   ```python
   _NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")


   def _has_node_id_marker(hint: object) -> bool:
       """Return True when ``hint`` is ``Annotated[T, NodeIDPrivate()]``.

       In the installed Strawberry, ``relay.NodeID[T]`` IS
       ``typing.Annotated[T, NodeIDPrivate()]`` — the explicit
       ``Annotated`` form and the ``relay.NodeID`` sugar collapse to the
       same shape, so ``typing.get_origin`` returns ``typing.Annotated``
       for both and the ``NodeIDPrivate`` instance lives in
       ``typing.get_args(...)``'s metadata slot.
       """
       return typing.get_origin(hint) is Annotated and any(
           isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint)
       )


   def _id_annotation_is_relay_node_id(cls: type) -> bool:
       """Return True when ``cls.__annotations__['id']`` resolves to ``relay.NodeID[...]``.

       Uses ``typing.get_type_hints(cls, include_extras=True)`` so
       stringified annotations (``from __future__ import annotations`` or
       explicit string annotations like ``id: "relay.NodeID[int]"``)
       evaluate against the consumer's module globals; ``include_extras``
       preserves the ``Annotated[T, NodeIDPrivate]`` marker.

       Fail-soft: ``typing.get_type_hints`` evaluates every annotation on
       ``cls`` and walks the MRO. A single unresolved string annotation
       anywhere on the class trips ``NameError``/``AttributeError`` even
       when ``id`` itself resolves cleanly. Two fail-soft sub-cases:

       1. ``id`` itself failed to resolve. ``cls.__annotations__["id"]``
          is the raw string the consumer wrote. Accept only when the
          string matches ``(?:^|\\.)NodeID\\[`` — qualified
          (``"relay.NodeID[int]"``) and unqualified (``"NodeID[int]"``)
          forms pass; prefixed-substring lookalikes (``"NotNodeID[int]"``,
          ``"MyNodeID[int]"``) and non-NodeID typos
          (``"MissingType"``) are rejected.
       2. Some other annotation tripped the exception but ``id`` is
          directly resolved. ``cls.__annotations__["id"]`` is the
          ``Annotated[int, NodeIDPrivate]`` object, not a string; fall
          back to ``_has_node_id_marker(raw)`` on the resolved object.
       """
       try:
           hints = typing.get_type_hints(cls, include_extras=True)
       except (NameError, AttributeError):
           raw = cls.__annotations__.get("id")
           if isinstance(raw, str):
               return bool(_NODEID_STRING_RE.search(raw))
           return _has_node_id_marker(raw)
       id_hint = hints.get("id")
       if id_hint is None:
           return False
       return _has_node_id_marker(id_hint)
   ```

   Rationale: per spec Decision 7 the helpers MUST live above `DjangoType` so the H1 guard inside `__init_subclass__` can call them. Module-scope keeps `_NODEID_STRING_RE` compiled once per process. The success path lives inside `_id_annotation_is_relay_node_id`'s try-block AFTER the except (rev8 M1) — Worker 2 must not split this into separate helpers.

3. **`django_strawberry_framework/types/base.py:98-114` — Replace the Decision 1 TODO block with the new `consumer_annotated_scalar_fields` collection.** Delete the entire TODO comment block (`# TODO(spec-015 Slice 1, Decision 1 — annotation-only scalar override collection):` through `#      membership (base.py:644 pre-Slice-1).`) and insert in its place:

   ```python
   consumer_annotated_scalar_fields = frozenset(
       field.name for field in fields if not field.is_relation and field.name in consumer_annotations
   )
   ```

   The insertion lands immediately after the existing `consumer_annotated_relation_fields` block at `:95-97`. Rationale: spec Decision 1 pins the two-comprehension parallel shape, and the spec's "no body edit in `_build_annotations`" claim depends on the new collection being in scope when the union below is built.

4. **`django_strawberry_framework/types/base.py:119-125` — Union the new set into `consumer_authored_fields`.** Add a fourth splat entry to the frozenset literal so it reads:

   ```python
   consumer_authored_fields = frozenset(
       {
           *consumer_annotated_relation_fields,
           *consumer_annotated_scalar_fields,
           *consumer_assigned_relation_fields,
           *consumer_assigned_scalar_fields,
       },
   )
   ```

   Rationale: spec Decision 2 places the new line between `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields` so the order groups annotation-side first (rev2 L1 ordering — annotations grouped, then assignments grouped).

5. **`django_strawberry_framework/types/base.py:126-207` — Replace the Decision 7 TODO block with the H1 Relay collision guard body.** Delete the entire TODO comment block (`# TODO(spec-015 Slice 1, Decision 7 — Relay id collision guard):` through `# for the full test list with the rev8 M2 unresolved-string recipe.`) and insert in its place the guard body. Transcribe verbatim from spec Decision 7 pseudocode (`spec:464-534`):

   ```python
   relay_shaped = any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)
   if relay_shaped:
       has_id_assignment = isinstance(cls.__dict__.get("id"), StrawberryField)
       has_id_annotation = "id" in cls.__annotations__
       if has_id_assignment:
           raise ConfigurationError(
               f"{cls.__name__}: cannot override the id field on a "
               "relay.Node-shaped type with an assigned strawberry.field. "
               "Use @classmethod resolve_id for a custom id resolver, "
               "id: relay.NodeID[<pk_type>] for a custom id annotation, "
               "or declare a resolver-backed sibling field — e.g., "
               "`@strawberry.field(description=...) def display_id(self) -> "
               "strawberry.ID: return str(self.pk)` — if you only need "
               "GraphQL field-level metadata on a custom identifier "
               "(a metadata-only sibling without a resolver builds but "
               "fails at query time); "
               "or remove relay.Node from Meta.interfaces.",
           )
       if has_id_annotation and not _id_annotation_is_relay_node_id(cls):
           raise ConfigurationError(
               f"{cls.__name__}: cannot override the id field on a "
               "relay.Node-shaped type without using strawberry.relay.NodeID[...]. "
               "The Relay interface supplies id: GlobalID! — declare the id "
               "field via relay.NodeID[<pk_type>] if you need a different id "
               "shape, or remove relay.Node from Meta.interfaces.",
           )
   ```

   Insertion site: between `consumer_authored_fields = ...` (post-step-4, immediately above) and `synthesized, pending = _build_annotations(...)` at currently `:208`. Rationale: spec Decision 7 pins the guard at class-creation time, after the four `consumer_*_fields` sets are built (so the guard can inspect annotations and assignments) and BEFORE `_build_annotations` runs (so the error fires before any synthesis side effects). Worker 2 must not move the guard inside `_build_annotations` (spec Decision 7 "Why `__init_subclass__` and not `_build_annotations`").

   Three error-message contracts pinned by the Slice 1 tests:
   - Assigned-side message MUST contain `"resolve_id"`, `"relay.NodeID"`, and one of `"display_id"` / `"sibling field"` (test `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises`).
   - Annotation-side message MUST contain `"relay.NodeID"` and `"GlobalID"` (tests `test_consumer_id_annotation_on_relay_node_type_raises`, `test_consumer_id_annotation_on_direct_relay_node_subclass_raises`, `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises`, `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`).

6. **`django_strawberry_framework/types/base.py:216-233` — Plumb `consumer_annotated_scalar_fields` through `DjangoTypeDefinition(...)`.** Inside the `DjangoTypeDefinition(...)` constructor call (currently `:216`-`:233`), add a `consumer_annotated_scalar_fields=consumer_annotated_scalar_fields,` kwarg between the existing `consumer_annotated_relation_fields=...` at `:228` and `consumer_assigned_relation_fields=...` at `:229`. The kwarg order matches the dataclass field order pinned in step 7 below (grouped-by-style: annotated-relation, annotated-scalar, assigned-relation, assigned-scalar).

7. **`django_strawberry_framework/types/definition.py:28-43` — Add `consumer_annotated_scalar_fields` field; re-order assigned-* lines.** Delete the entire TODO comment block at `:30-41` (`# TODO(spec-015 Slice 1, rev2 L1 — grouped-by-style ordering):` through `# read this set directly.`). The post-Slice-1 shape is, per spec Decision 3 sample:

   ```python
   consumer_authored_fields: frozenset[str] = frozenset()
   consumer_annotated_relation_fields: frozenset[str] = frozenset()
   consumer_annotated_scalar_fields: frozenset[str] = frozenset()
   consumer_assigned_relation_fields: frozenset[str] = frozenset()
   consumer_assigned_scalar_fields: frozenset[str] = frozenset()
   ```

   The existing `consumer_assigned_relation_fields` and `consumer_assigned_scalar_fields` lines (currently `:42-43`) stay where they are; the new `consumer_annotated_scalar_fields` line sits at the position the TODO marked — between `consumer_annotated_relation_fields` (`:29`) and `consumer_assigned_relation_fields` (`:42` pre-Slice-1, becomes `:31` post-edit). No cosmetic re-order of the existing assigned-* lines is needed because the spec's grouped-by-style order (annotated-relation, annotated-scalar, assigned-relation, assigned-scalar) is what the current file naturally achieves once the new field lands at the TODO's insertion point — Worker 1 verified the current file shape is already grouped-by-style and the spec L1 fix only requires the new field to land in the gap. The "cosmetic re-order" wording in spec Slice 1 sub-bullet 2 anticipated a different starting layout; the current file is already in the right shape.

8. **`pyproject.toml:108-113` — Remove the temporary per-file-ignores.** Delete the four lines at `:108-113`:

   ```
   # Temporary: spec-015 Slice 1 TODO anchors carry pseudo-code blocks that trip
   # ERA001. Remove these two entries when Slice 1 lands and the TODO bodies are
   # replaced by real code (see docs/spec-015-consumer_overrides_scalar-0_0_6.md
   # revision 10 L2).
   "django_strawberry_framework/types/base.py" = ["ERA001"]
   "django_strawberry_framework/types/definition.py" = ["ERA001"]
   ```

   Rationale: spec rev10 L2 — the per-file-ignores were the temporary mechanism for keeping lint clean while the TODO pseudo-code blocks lived in the tree. Steps 3, 5, and 7 above replace the TODO bodies with real code in this slice's commit; the per-file-ignores must come out atomically so `ruff check .` continues to pass against the post-Slice-1 source. Worker 2 confirms via `uv run ruff check .` that no `ERA001` violations surface in `types/base.py` / `types/definition.py` after the deletion.

9. **`tests/types/test_definition_order.py:312-428` — Replace the Slice 1 cluster TODO block with the 18 new tests.** Delete the entire TODO comment block from `:312` (`# TODO(spec-015 Slice 1 — 18 of 19 Slice 1 tests land here):`) through `:428` (the last sub-bullet recipe for `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`) and replace it with the 18 test functions named in the spec. Worker 2 also adds the test-module imports the spec recipe names: at the top of the file, add to the existing import block:

   ```python
   import re
   import sys
   import types
   import uuid

   from strawberry import relay
   from strawberry.relay.types import NodeIDPrivate
   ```

   And the `_FakeUnsupportedField` fixture at the top of the test file (after the existing helper at `:21-30`, before the first test at `:33`), per rev9 L2 + rev10 L1 mandatory placement in `test_definition_order.py`:

   ```python
   class _FakeUnsupportedField(models.Field):
       """One-line Django Field subclass with no SCALAR_MAP match; pins the
       unsupported-field-type bypass test (spec-015 Slice 1, Decision 7a).
       """
   ```

   (Worker 2 adds `from django.db import models` to the imports if not present — it currently is not at the top of the file; the existing test file imports from `apps.products.models` and `apps.library.models` but does not directly import `models`.)

   The 18 test bodies pin the assertion shapes documented in step 10 below. Test functions land between the existing `test_assigned_scalar_field_override_keeps_consumer_resolver` at `:278-309` and `test_scalar_field_class_attribute_shadowing_raises` at `:429`.

10. **`tests/types/test_converters.py:1040-1071` — Replace the ArrayField bypass TODO block with the 19th test.** Delete the entire TODO comment block from `:1040` (`# TODO(spec-015 Slice 1, rev6 L3 — placement in test_converters.py):`) through `:1071` (`# (un-overridden nested arrays continue to raise).`) and replace it with `test_annotation_override_of_arrayfield_with_nested_array_is_allowed`. The test body uses `_FakeArrayField` (at `:449`) and the `_ARRAY_FIELD_CLS` monkeypatch idiom; per rev4 L2 the model field name and consumer annotation name must both be `arr`.

### Test additions / updates

19 new tests total for Slice 1: 18 in `tests/types/test_definition_order.py` + 1 in `tests/types/test_converters.py` (matches the spec's "18 of 19 land in `test_definition_order.py`" + "1 of 19 in `test_converters.py`" pinning at `spec:782` and the test_converters.py TODO at `:1040`).

**`tests/types/test_definition_order.py` — 18 new tests + `_FakeUnsupportedField` fixture:**

**Four core override tests:**

- `test_annotation_only_scalar_field_override_wins_over_synthesized` — declare `CategoryType(DjangoType)` with `description: int` and `Meta: model=Category, fields=("id","name","description")`. Pre-finalize assert `CategoryType.__annotations__["description"] is int`. Call `finalize_django_types()`. Post-finalize assert `CategoryType.__annotations__["description"] is int` (the merge at `types/base.py:138` puts consumer last). Optionally inspect the strawberry definition: `_strawberry_field(CategoryType, "description").type` is `int`.

- `test_annotation_only_scalar_override_populates_definition_metadata` — same `CategoryType` shape as above. Assert `definition = CategoryType.__django_strawberry_definition__`; `definition.consumer_annotated_scalar_fields == frozenset({"description"})`; `definition.consumer_authored_fields >= frozenset({"description"})`; `definition.consumer_assigned_scalar_fields == frozenset()`. Pins the new introspection field and the union shape.

- `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation` — same `CategoryType` shape. Call `_build_annotations(...)` directly (whitebox) — import `_build_annotations` from `django_strawberry_framework.types.base`. Assert the synthesized dict (first return-tuple element) does NOT contain `"description"`. Rationale: pins the short-circuit path. Imports needed at test top: `from django_strawberry_framework.types.base import _build_annotations`.

- `test_annotation_only_scalar_override_survives_strawberry_finalization` — declare `CategoryType` with `description: int` and `Meta` selecting `"description"`. Define `@strawberry.type class Query: category: CategoryType`. Call `finalize_django_types()`. Build `strawberry.Schema(query=Query)`. Execute introspection query `{ __type(name: "CategoryType") { fields { name type { kind name ofType { kind name } } } } }`. Walk to the `description` entry; assert `type.kind == "NON_NULL"` and `type.ofType.name == "Int"`. Worker 2 may reuse the existing `_introspect_field_type` helper at `tests/types/test_converters.py:434-446` by importing it — but that creates a cross-file test dependency Worker 1 finds slightly awkward; recommended path is to inline the introspection query in this single test (the surrounding tests at `:278` already inline introspection-shaped queries).

**Four converter-bypass tests** (per spec Decision 7a):

- `test_annotation_override_of_unsupported_scalar_field_type_is_allowed` — define inline model with a `_FakeUnsupportedField()` field (the fixture added at the top of the file). Confirm without override: declaring a `DjangoType` selecting that field raises `ConfigurationError`. With consumer `myfield: str` annotation, assert no error at class creation; assert `definition.consumer_annotated_scalar_fields` contains the field name; assert `finalize_django_types()` succeeds. Per rev2 M1: use `str` (or `int`), NOT `bytes`. The "without override fails" half may be implemented as a `pytest.raises(ConfigurationError)` smoke at the top of the test body so the bypass-is-relative-to-the-baseline contract is explicit.

- `test_annotation_override_of_grouped_choices_field_is_allowed` — declare a Django model with a `CharField(choices=[("group1", [("a", "A"), ("b", "B")])])`. With consumer `status: str` annotation, assert no error is raised at class creation; assert `finalize_django_types()` succeeds; assert `registry.get_enum(model, "status") is None`. Imports: `from django_strawberry_framework.registry import registry`.

- `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` — declare one Django model `M` with a non-grouped `status = CharField(choices=[("a","A"),("b","B")])`. Declare two DjangoTypes: `OverrideType(DjangoType)` with `class Meta: model = M; primary = True; fields = ("status",)` and a consumer `status: str` annotation; `NonOverrideType(DjangoType)` with `class Meta: model = M; fields = ("status",)` (no override). `finalize_django_types()`. Assert: (a) `registry.get_enum(M, "status")` returns a non-`None` enum class; (b) `strawberry.Schema(...)` builds; introspecting `NonOverrideType.status` returns the generated enum's GraphQL name; (c) introspecting `OverrideType.status` returns `String!`. Pins both halves of the cross-type cache contract (rev6 L2 + rev8 L2 mandatory placement in `test_definition_order.py`).

**Eleven Relay-collision tests** (per spec Decision 7):

The five **reject** paths:

- `test_consumer_id_annotation_on_relay_node_type_raises` — declare `class CategoryNode(DjangoType): id: int; class Meta: model = Category; fields = ("id","name"); interfaces = (relay.Node,)`. Assert `ConfigurationError` raised at class definition (use `pytest.raises(ConfigurationError, match=...)`) with the match expression covering both `"relay.NodeID"` and `"GlobalID"` (two separate `with pytest.raises(ConfigurationError) as exc_info:` + post-block `assert "relay.NodeID" in str(exc_info.value) and "GlobalID" in str(exc_info.value)` is the cleaner shape).

- `test_consumer_id_annotation_on_direct_relay_node_subclass_raises` (rev8 H1) — declare `class DirectRelayChild(DjangoType, relay.Node): id: int; class Meta: model = Category; fields = ("id","name")` (NO `Meta.interfaces` line). Assert `ConfigurationError` with the same `"relay.NodeID"` + `"GlobalID"` message contract. Pins the `issubclass(cls, relay.Node)` half of the guard predicate.

- `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises` — declare a DjangoType with `Meta.interfaces = (relay.Node,)` and either `id = strawberry.field(resolver=lambda root: "x")` or the decorator form `@strawberry.field def id(self) -> relay.GlobalID: ...`. Assert `ConfigurationError`. Assert message contains all three of `"resolve_id"`, `"relay.NodeID"`, and one of `"display_id"` / `"sibling field"`. Recipe note: the assigned-`id` is shadowed by both `cls.__dict__.get("id")` and `cls.__annotations__["id"]` (via the decorator's type annotation), so the assigned branch fires first and raises — the test pins that the assigned-side error message wins.

- `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` — declare `class CategoryNode(DjangoType): id: "MissingType"; class Meta: model = Category; fields = ("id","name"); interfaces = (relay.Node,)`. Where `MissingType` is not imported and not a NodeID. Assert `ConfigurationError` with `"relay.NodeID"` + `"GlobalID"` message contract. Pins the rev5 M1 + rev7 H1 contract: `typing.get_type_hints` raises `NameError`, fail-soft inspects raw string `"MissingType"`, regex match fails, helper returns False, guard raises.

- `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` (rev7 H1) — declare a DjangoType with `id: "NotNodeID[int]"` annotation and `Meta.interfaces = (relay.Node,)`. Assert `ConfigurationError`. Worker 2 also adds a second assertion (or parametrizes the test) for `id: "MyNodeID[int]"`. Pins that the `(?:^|\.)NodeID\[` regex requires start-of-string or dot-boundary — the substring `NodeID[` inside `NotNodeID[` and `MyNodeID[` does NOT match.

The six **accept** paths:

- `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` — declare a DjangoType with `id: relay.NodeID[int]` and `Meta.interfaces = (relay.Node,)`. Assert no `ConfigurationError` at class creation; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(query=Query)` builds for some trivial Query.

- `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` (rev7 H1) — declare a DjangoType with an explicit stringified `id: "relay.NodeID[int]"` annotation and `Meta.interfaces = (relay.Node,)`. The test file's module scope MUST have `from strawberry import relay` imported (it already will because of the other Relay tests). Assert no `ConfigurationError`; assert finalize + schema build succeed; introspect the `id` field and assert `kind == "NON_NULL"`, `ofType.name == "ID"` (the Relay-supplied `id: GlobalID!`). Pins the resolved-string end-to-end contract.

- `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` (rev7 H1 + rev8 M2 + rev9 L1 + rev10 M2) — MANDATORY recipe per rev8 M2. Use the recipe from spec `:115` and the in-tree TODO at `tests/types/test_definition_order.py:387-416` verbatim: (1) generate `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"`; (2) `sys.modules[stub_name] = types.ModuleType(stub_name)`; assert no `"relay"` key in the stub's `__dict__`; (3) define `_body(ns)` callable that sets `ns["__module__"] = stub_name`, `ns["__annotations__"] = {"id": "relay.NodeID[int]"}`, and creates a nested `class _Meta: model = Category; interfaces = (relay.Node,)` assigned to `ns["Meta"]`; (4) call `types.new_class("UnresolvedRelayChild", (DjangoType,), {}, _body)`; assert the call returns without raising; (5) wrap the entire body in `try/finally` calling `sys.modules.pop(stub_name, None)` AND `registry.clear()` in the `finally` block (rev9 L1 + rev10 M2: both are required to prevent leaking the synthesized class into co-resident type tests). Do NOT call `finalize_django_types()` or `strawberry.Schema(...)` — the test contract is "class creation succeeds; downstream resolution is the consumer's responsibility".

- `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` (rev6 H1) — declare a DjangoType with `id: relay.NodeID[int]` AND `items: list["AdminItemType"]` (where `AdminItemType` is not defined / not imported), and `Meta.interfaces = (relay.Node,)`. Assert no `ConfigurationError` at class creation. Rationale: `typing.get_type_hints` raises `NameError` because of the sibling, fail-soft sub-case 2 fires, `cls.__annotations__["id"]` is the resolved `Annotated[int, NodeIDPrivate]` object (not a string), `_has_node_id_marker(raw)` returns True, guard accepts.

- `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` — declare `class CategoryNode(DjangoType): description: int; class Meta: model = Category; fields = ("id","description"); interfaces = (relay.Node,)`. Assert no `ConfigurationError` raised. Pins that the guard is keyed on the GraphQL field name `"id"`, not on the model's pk name. Per rev6 L3: use the `description: int` recipe as the default (not the monkeypatched-`code`-pk alternative).

- `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` (rev6 L1 + rev7 M1) — declare a `class BaseWithId(DjangoType): id: int` (no `Meta`, so `__init_subclass__` short-circuits at the `if meta is None: return` check at `types/base.py:81`). Then declare `class ChildRelayType(BaseWithId): class Meta: model = Category; interfaces = (relay.Node,); fields = ("id", "name")`. Assert: (a) no `ConfigurationError` at class creation; (b) `strawberry.Schema(query=Query, types=[ChildRelayType])` succeeds (build a trivial `Query` that returns `ChildRelayType`); (c) introspecting `ChildRelayType.id` returns `kind == "NON_NULL"` with `ofType.name == "ID"` (Relay-supplied interface field). Optionally: assert `ChildRelayType.resolve_id_attr() == "pk"`. Per rev7 M1 inversion: the contract is "Strawberry schema succeeds" — pk-suppression handles the inherited annotation silently.

**`tests/types/test_converters.py` — 1 new test:**

- `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` — recipe from the in-tree TODO at `:1049-1071`. Use the `_FakeArrayField` fixture (at `:449`), the `_ARRAY_FIELD_CLS` monkeypatch idiom, and an `arr` model-field name + `arr: list[list[int]]` consumer annotation (rev4 L2 — names MUST match). Confirm `finalize_django_types()` succeeds after the override. Worker 2 also confirms the existing `test_array_field_multidim_rejected_via_fake_sentinel` at `:1021` still passes (un-overridden nested arrays continue to raise).

**Test count verification.** 18 in `test_definition_order.py` + 1 in `test_converters.py` = 19 total. Matches spec rev10 `:744` ("Slice 1 test cluster has 19 tests total") and the implementation-plan table at `:723` ("19 new tests: 4 core + 4 converter-bypass + 11 Relay").

### Implementation discretion items

The spec is heavily prescriptive — most "Worker 1 picks during planning" hedges were already resolved at higher revisions. Worker 1 explicitly resolves the remaining items here:

- **`_FakeUnsupportedField` fixture placement.** Spec rev9 L2 + rev10 L1 mandate `tests/types/test_definition_order.py`. Worker 1 confirms placement at the top of that file (after `_strawberry_field` at `:30`, before the first test at `:33`). The "alternative existing Django field" branch is NOT used; the synthetic fixture is the default per rev10 L1.

- **Cross-type cache test placement.** Spec rev8 L2 mandates `tests/types/test_definition_order.py`. No discretion remains.

- **`_introspect_field_type` reuse in `test_annotation_only_scalar_override_survives_strawberry_finalization`.** Worker 1 recommends inlining the introspection query in the test body rather than cross-importing the helper from `test_converters.py`. The recommendation is at Worker 2's discretion: either path produces an equivalent test contract. Cross-importing is acceptable if it reduces test-body line count materially; planning's slight preference is for inline.

- **`pytest.raises` shape for the Relay-collision reject tests.** Worker 1 recommends `with pytest.raises(ConfigurationError) as exc_info: ...` followed by post-block `assert "...keyword..." in str(exc_info.value)` rather than the `match=r"..."` regex form. Reason: the spec pins three keywords (`"resolve_id"`, `"relay.NodeID"`, `"display_id"` / `"sibling field"`) for the assigned-side test; expressing three keyword conjunctions in a single regex is brittle. Worker 2 picks; either shape satisfies the spec.

- **`tests/types/test_definition_order.py` model import strategy.** The current test file imports `Category, Entry, Item, Property` from `apps.products.models` at `:6`. The unsupported-field-type test and grouped-choices test need ad-hoc inline `class TestModel(models.Model): ...` declarations to keep model-side configuration local to the test. Worker 2 adds `from django.db import models` to the imports and follows the inline-model pattern that exists in `tests/types/test_converters.py:483-484` (`class BigIntOwner(models.Model): ... class Meta: managed = False; app_label = "test_bigint"`). Equally valid pattern: derive a temporary subclass from `Category`; planning prefers the inline-model form because it keeps the test self-contained.

- **Decorator-form vs assignment-form for the assigned-`id` reject test.** Either `id = strawberry.field(resolver=lambda root: "x")` or `@strawberry.field def id(self) -> relay.GlobalID: ...` shapes will trip `isinstance(cls.__dict__.get("id"), StrawberryField)`. Worker 2 picks; the spec's intent is "the assigned-id path raises regardless of declaration form". Planning's slight preference is the explicit assignment form for readability.

No architectural questions remain unresolved.

### Spec slice checklist (verbatim)

- [x] In `django_strawberry_framework/types/base.py:95-108`, collect a new `consumer_annotated_scalar_fields` frozenset in `DjangoType.__init_subclass__` parallel to `consumer_annotated_relation_fields`. Walks the same `consumer_annotations = dict(getattr(cls, "__annotations__", {}))` mapping but filters on `not field.is_relation` instead of `field.is_relation`. (See [Decision 1](#decision-1--annotation-only-scalar-override-collection).)
- [x] Add `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` field to `django_strawberry_framework/types/definition.py:DjangoTypeDefinition` in the **grouped-by-style** order (L1 fix; matches Decision 3's sample): annotated-relation, annotated-scalar, assigned-relation, assigned-scalar. Worker 1 lands the cosmetic re-order of the existing two `consumer_assigned_*` lines in the same commit as the new field so the dataclass field order is internally consistent.
- [x] Union the new set into the existing `consumer_authored_fields` frozenset at `types/base.py:102-108`. The scalar branch of `_build_annotations` already short-circuits on `consumer_authored_fields` membership (`types/base.py:644`) — once annotation-only scalars are members, synthesis is skipped for them, and the existing post-merge line `cls.__annotations__ = {**synthesized, **consumer_annotations}` at `types/base.py:138` leaves the consumer's annotation untouched. **No change to `_build_annotations` body.**
- [x] Plumb the new set through to `DjangoTypeDefinition` at the registration call site (`types/base.py:117-134`).
- [x] **Module-scope helpers for the H1 guard (rev8 M1 + rev9 L3 — implementation order).** Land these in `django_strawberry_framework/types/base.py` **above** `DjangoType`'s class definition, before the H1 guard bullet below. The guard body below calls `_id_annotation_is_relay_node_id(cls)`, which calls `_has_node_id_marker(...)`, which uses `_NODEID_STRING_RE` — all three must exist at module scope when the guard executes. Imports to add at the top of `types/base.py`: `re`, `typing`, `Annotated` from `typing`, and `NodeIDPrivate` from `strawberry.relay.types`. The three definitions (full bodies in [Decision 7](#decision-7--relay-id-override-collision)'s pseudocode block, rev8 M1 — structure pinned: regex at module scope, `_has_node_id_marker` as the `Annotated + NodeIDPrivate` check, success path inside `_id_annotation_is_relay_node_id`'s try-block after the except clause):
  - [x] `_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")` — module-scope (compiled once per process).
  - [x] `def _has_node_id_marker(hint: object) -> bool:` returning `typing.get_origin(hint) is Annotated and any(isinstance(arg, NodeIDPrivate) for arg in typing.get_args(hint))`.
  - [x] `def _id_annotation_is_relay_node_id(cls: type) -> bool:` with the try-except `typing.get_type_hints(cls, include_extras=True)` structure and the success path AFTER the except clause (rev8 M1).
- [x] **Relay `id` collision guard (H1 fix, rev4 pinned class-creation-time + assigned-id rejection; rev6 sibling-field workaround in error message + rev6 H1 fail-soft fix).** After the `consumer_annotated_scalar_fields` / `consumer_assigned_scalar_fields` collections are built but before `_build_annotations` is invoked, detect: (a) `interfaces` (from `_validate_meta`) includes `relay.Node` — checked the same way `_build_annotations` does it at `types/base.py:609` (pre-Slice-1), via `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`; AND (b) the consumer authored an entry for the GraphQL field name `"id"` — either an annotation (`"id" in cls.__annotations__` — rev4 M2: key-presence rather than value-truthiness so unusual annotations like `id: None`, `id: Literal[None]`, or string forms that evaluate to false-y types are also detected; rev6 M3 corrected the rev4 M2 rationale, which described the value as "literally None" — Python actually evaluates `None` to `<class 'NoneType'>`) or an assignment (`isinstance(cls.__dict__.get("id"), StrawberryField)`). Two reject paths:
  - **Assigned `id = <StrawberryField>`**: always rejected on a Relay-Node-shaped type. The error message names three supported alternatives (rev6 M1 + rev7 M2): `@classmethod resolve_id` for a custom id resolver, `id: relay.NodeID[<pk_type>]` for a custom id annotation, and a **resolver-backed sibling field** — e.g., `@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)` — for the field-level GraphQL metadata use case (rev4 M1 banned `id = strawberry.field(description="…")`, rev6 M1 acknowledged this removed the only field-metadata path for the Relay-supplied `id`, and rev7 M2 corrected the workaround example from the metadata-only `display_id: ID = strawberry.field(description="…")` form — which would build but fail at query time because `display_id` is not a Django attribute on the model instance — to the resolver-backed form that carries the metadata AND defines a value source). Rev4 M1: this is a small intentional behavior change — previously consumers could write `@strawberry.field def id(self) -> relay.GlobalID: ...` and Strawberry would accept it. This card bans that pattern uniformly.
  - **Annotation `id: <type>` where `<type>` is not `relay.NodeID[...]`**: rejected. Detection of "is `relay.NodeID[...]`" uses `typing.get_type_hints(cls, include_extras=True)` (NOT raw `typing.get_args(cls.__annotations__["id"])`) so stringified annotations and PEP 563 (`from __future__ import annotations`) forms are evaluated against `cls`'s module globals. Fail-soft on `NameError`/`AttributeError`: the fail-soft scoping covers two sub-cases — (i) the `id` annotation itself is an unresolved string, accept only when the string matches the rev7 H1 token-shaped regex `(?:^|\.)NodeID\[` (not the rev6 plain-substring `"NodeID["` check, which accepted prefixed-substring lookalikes like `"NotNodeID[int]"` as false positives); (ii) some OTHER annotation on the class failed to resolve while `id` is directly resolved (rev6 H1 fix: fall back to `_has_node_id_marker(raw)` rather than rejecting on the not-a-string branch — the rev5 logic falsely rejected valid escape hatches in this case). The fail-soft accept window in sub-case (i) is package-level guard suppression only — Strawberry's downstream schema construction still resolves the same string against `cls`'s module globals and may fail there if the consumer hasn't made the symbol importable. The error message points at `relay.NodeID[<pk_type>]` as the supported escape hatch. (See [Decision 7](#decision-7--relay-id-override-collision) for the detection-helper pseudocode and the dropped finalize-time alternative.) **Important: the predicate is keyed off the GraphQL field name `"id"`, not the model's pk name.** A model with `code = models.CharField(primary_key=True)` and a consumer `code: str` override does NOT trigger the guard — the GraphQL fields are `id: ID!` (from Relay) and `code: String!` (from the consumer), no collision.
- [x] Tests in `tests/types/test_definition_order.py` (the existing override-contract host, where the three relation-override tests at `:179`, `:206`, `:235` live, plus the `:278` `test_assigned_scalar_field_override_keeps_consumer_resolver` test). The annotation-only scalar contract is the natural fourth sibling; placement matches the existing relation/scalar/annotation/assigned 2×2 matrix:
  - [x] `test_annotation_only_scalar_field_override_wins_over_synthesized` (the headline test for this card): declare a `DjangoType` with a Django `CharField` selected and a consumer annotation `description: int` shadowing it. Pre-finalize, assert `cls.__annotations__["description"] is int`. Post-finalize, assert the same — and assert the Strawberry definition's field type matches the consumer's annotation, not the auto-synthesized `str`. This is the test currently skipped at `tests/types/test_base.py:444-465` (rename / move and unskip — see Slice 2).
  - [x] `test_annotation_only_scalar_override_populates_definition_metadata`: assert `definition.consumer_annotated_scalar_fields == frozenset({"description"})`, `definition.consumer_authored_fields >= frozenset({"description"})`, and `definition.consumer_assigned_scalar_fields == frozenset()` (annotation-only, no assignment).
  - [x] `test_annotation_only_scalar_override_does_not_emit_synthesized_annotation`: assert the synthesized annotations dict returned by `_build_annotations` does NOT contain `"description"` for the override case. (Pins that the short-circuit fires; without this we could still merge consumer-over-synthesized but the side-effect of double-walking the field path could regress later.)
  - [x] `test_annotation_only_scalar_override_survives_strawberry_finalization` (M1 fix — unwrap through `NON_NULL`): the historical skip-reason at `tests/types/test_base.py:444-453` claimed Strawberry's `@strawberry.type` decorator regenerates `cls.__annotations__` after our merge. The current `__init_subclass__` already merges `{**synthesized, **consumer_annotations}` at `types/base.py:138` (consumer last so consumer wins), but the pre-Slice-1 single-source `synthesized` dict still contained the auto-mapped scalar annotation for the field name. Under this card, the synthesized dict no longer contains the consumer-overridden field, so the merge degenerates to "consumer annotation only" — no Strawberry-side regeneration can override it because there's nothing for it to fall back to. This test calls `[finalize_django_types](GLOSSARY.md#finalize_django_types)()`, builds a `strawberry.Schema(query=Query)` with a query field returning the type, and runs `schema.execute_sync(...)` against an introspection query of the shape `__type(name: "<TypeName>") { fields { name type { kind name ofType { kind name } } } }`. A non-nullable Django scalar surfaces in GraphQL as `Int!` — `type.kind == "NON_NULL"` and `type.name is None`; the terminal scalar name (`"Int"`) lives at `type.ofType.name`. The test unwraps through `NON_NULL` and asserts the terminal `ofType.name` matches the consumer's annotation. Worker 1 may instead reuse the existing `_introspect_field_type` helper pattern at `tests/types/test_converters.py:434` if the surface is a closer fit — the contract is "unwrap to the terminal type and assert that". Pins the end-to-end contract.
  - [x] **Converter-bypass regressions (H2 fix; four new tests, rev6 L2 — added cross-type cache test).** The new short-circuit skips `convert_scalar(...)` for the overridden field, which means every converter-side validation and side effect is bypassed for that field. The bypass is the intended consumer-authoritative contract (see [Decision 7a](#decision-7a--converter-validation-bypass-h2-fix)), but the spec needs explicit tests that pin it so future readers understand the surface and so converter changes do not silently re-introduce validation against an overridden field:
    - [x] `test_annotation_override_of_unsupported_scalar_field_type_is_allowed` (rev2 M1 — use Strawberry-supported consumer annotation; rev9 L2 — explicit fixture creation; rev10 L1 — placement mandatory): **Worker 1 first adds** a minimal `_FakeUnsupportedField(models.Field)` fixture at the top of `tests/types/test_definition_order.py` — placement is mandatory per rev10 L1 (the rev9 L2 "or `tests/types/test_converters.py` if Worker 1 prefers" allowance was dropped because the "18-of-19 Slice 1 tests land in `test_definition_order.py`" rule must stay true; only the nested-`ArrayField` bypass test gets the converter-host exception, and that exception has a concrete fixture-locality reason — `_FakeArrayField` already lives there). The fixture is a one-line `Field` subclass whose MRO has no `SCALAR_MAP` match — `_FakeUnsupportedField` does NOT exist in the test tree pre-Slice-1, so this is a real fixture-creation step, not a "use the existing one" reference. (Alternative: a concrete existing Django field whose MRO has no `SCALAR_MAP` match — Worker 1 verifies via `grep` during planning; the synthetic fixture is the recommended default because it keeps the test self-documenting.) Then declare a `DjangoType` selecting that field. Without the override, `convert_scalar` raises `ConfigurationError`. With a consumer `myfield: str` annotation (or `int` — any Strawberry-supported scalar annotation; **NOT** `bytes`, which Strawberry's schema-construction pass rejects as an unexpected Python type and would create a false test failure unrelated to the bypass contract), assert: (a) no error is raised at class-creation time, (b) `definition.consumer_annotated_scalar_fields` contains the field name, and (c) `finalize_django_types()` succeeds. The consumer's override is the recourse for unsupported scalars; `Meta.exclude` is still the recourse for "drop the field entirely".
    - [x] `test_annotation_override_of_grouped_choices_field_is_allowed`: declare a `DjangoType` selecting a Django `CharField` with grouped `choices=[("group1", [("a", "A"), ("b", "B")])]`. Without the override, `convert_choices_to_enum` raises `ConfigurationError` containing `"grouped-choices"` (existing test `tests/types/test_converters.py:test_grouped_choices_form_rejected` pins this). With a consumer `status: str` annotation, assert no error is raised, the type is finalizable, and `registry.get_enum(model, "status")` is `None` (enum registration is bypassed along with annotation synthesis).
    - [x] `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` (rev3 M2 placement; rev4 L2 name-match; rev6 L3 — placement (a) is the default): real `django.contrib.postgres.fields.ArrayField` testing requires the `_ARRAY_FIELD_CLS` monkeypatch + `_FakeArrayField` fixture pattern that lives in `tests/types/test_converters.py:449-1100` (every existing `ArrayField` test uses it; the production code at `types/converters.py:91` soft-imports the real class and CI environment-dependence is the failure mode without the monkeypatch). **Default: place this single test in `tests/types/test_converters.py` beside the existing `_FakeArrayField` tests** so the fixture lookup stays local (smaller-touch). The alternative (b) — placement in `tests/types/test_definition_order.py` with a re-import or duplicate of `_FakeArrayField` — is no longer recommended; Worker 1 may pick (b) only if a planning-time concern surfaces. **The model-field name and the consumer-annotation name MUST match** (rev4 L2) — mirror the existing converter tests' `arr`-named field, so the consumer annotation is `arr: list[list[int]]`. A name mismatch means the override-collection path never fires (the consumer annotation does not name a selected model field) and the test exercises the rejection path instead — false-passing for the wrong reason. Test body: `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)`; build a `_FakeArrayField(_FakeArrayField(models.IntegerField()))` instance registered as a model field named `arr`; declare a `DjangoType` selecting that field with a consumer `arr: list[list[int]]` annotation; assert no error is raised at class-creation time and `finalize_django_types()` succeeds. Verify that the existing `tests/types/test_converters.py:1021` nested-array rejection test still passes (un-overridden nested arrays still raise).
    - [x] `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` (rev6 L2 — cross-type cache behavior change): pins the rev5 Decision 7a flag that two `DjangoType`s on the same model with the same `choices=` column — one overriding and one not — get the fresh enum from the non-overriding type alone. Declare a single Django model with a non-grouped `status` `CharField(choices=[...])`. Declare two `DjangoType`s on that model: `OverrideType` with `class Meta: model = M; primary = True; fields = ("status",)` and a consumer `status: str` annotation (override); `NonOverrideType` with `class Meta: model = M; fields = ("status",)` (no override). `finalize_django_types()`. Assert: (a) `registry.get_enum(model, "status")` returns a non-`None` enum class (populated by `NonOverrideType`'s `convert_scalar` call); (b) building a `strawberry.Schema` and introspecting `NonOverrideType.status` returns the generated enum's GraphQL name; (c) introspecting `OverrideType.status` returns `String!` (the consumer's annotation). Pins both halves of the contract — the bypass on the overriding type does not poison the cache for the non-overriding type, and the cache entry from the non-overriding type does not leak into the overriding type's GraphQL surface. **Test placement: `tests/types/test_definition_order.py` — mandatory per rev8 L2.** Rev6 L2 / rev7 framed this as a Worker 1 choice between `test_definition_order.py` (default) and `test_converters.py`, but the test exercises override-vs-non-override cross-talk — not converter-internal behavior — so it belongs with the rest of the override-contract matrix. The `test_converters.py` alternative is dropped.
- [x] **Relay collision tests (H1 fix; ten new tests, rev6 + rev7 expanded — rev6 added H1 sibling-annotation accept and L1 inheritance non-trigger; rev7 split the stringified-NodeID accept test into resolved-end-to-end and unresolved-guard-only variants, added a typo-lookalike reject test, and inverted the inheritance test to assert schema succeeds via pk-suppression).** New tests in `tests/types/test_definition_order.py` alongside the four-corner cluster:
  - [x] `test_consumer_id_annotation_on_relay_node_type_raises`: declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an `id: int` (or `id: str`) consumer annotation. Assert `ConfigurationError` raised at class-creation time (before `finalize_django_types()`), with message containing both `"relay.NodeID"` and `"GlobalID"`. Pins the early-raise contract for the `Meta.interfaces` declaration shape; without H1's guard, the consumer would see a Strawberry-side `ValueError` only at `strawberry.Schema(...)` construction, which is the wrong UX surface.
  - [x] `test_consumer_id_annotation_on_direct_relay_node_subclass_raises` (rev8 H1): declare a `DjangoType` that directly subclasses `relay.Node` — i.e., `class DirectRelayChild(DjangoType, relay.Node): id: int; class Meta: model = Category; fields = ("id", "name")` (NO `Meta.interfaces` line). Assert `ConfigurationError` raised at class-creation time with the same message contract as the `Meta.interfaces` variant (both `"relay.NodeID"` and `"GlobalID"` in the message). Pins the second half of the rev7 Decision 7 guard predicate (`any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`) — without this test, an implementation that wired only the `interfaces` half (forgetting the `issubclass(cls, relay.Node)` disjunct) would pass every other Slice 1 Relay-collision test while leaving `class CategoryNode(DjangoType, relay.Node): id: int` to fall through to the downstream Strawberry `ValueError`. Worker 1 may parametrize `test_consumer_id_annotation_on_relay_node_type_raises` over both declaration styles instead of adding a separate test; the contract is "the annotation reject path fires for both shapes". Note: the assigned-`id` reject path is NOT parametrized over direct-inheritance shape (rev8 H1: optional symmetry; the high-value pin is annotation-side); Worker 1 may add a `test_consumer_id_assigned_strawberry_field_on_direct_relay_node_subclass_raises` companion if planning surfaces value but the spec doesn't mandate it.
  - [x] `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises` (rev4 M1 assigned-id rejection; rev6 M1 + rev7 M2 sibling-field workaround in error message): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an assigned `id = strawberry.field(resolver=...)` (or `@strawberry.field def id(self) -> relay.GlobalID: ...` decorator-style). Assert `ConfigurationError` raised at class-creation time with message containing **all three** of `"resolve_id"`, `"relay.NodeID"`, and one of `"display_id"` / `"sibling field"` (rev7 M2 — the resolver-backed sibling field is the documented workaround for the metadata-only assigned-`id` use case). Pins the intentional ban on assigned `id` overrides on Relay-Node-shaped types and the rev6 M1 + rev7 M2 resolver-backed sibling-field workaround in the error message.
  - [x] `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` (rev5 M1 unresolved-non-NodeID-string rejection): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a stringified `id: "MissingType"` annotation (where `MissingType` is not imported and not a NodeID — e.g., a typo or a forward reference to a non-existent class). Assert `ConfigurationError` raised at class-creation time with message containing both `"relay.NodeID"` and `"GlobalID"`. Pins the narrow rev5 fail-soft contract under the rev7 H1 tightened predicate: `typing.get_type_hints` raises `NameError` for this annotation, the helper inspects the raw string at `cls.__annotations__["id"]`, fails to match the `(?:^|\.)NodeID\[` regex, and rejects. Without this test, a typo like `id: "Stirng"` would slip past the guard at class-creation time and surface only as a Strawberry schema-construction error later — exactly the failure mode H1 exists to prevent. (The companion rev7 `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` covers the rev7 H1 regex-specific rejection of prefixed-substring lookalikes like `"NotNodeID[int]"`; this rev5 test covers the broader "non-NodeID-shaped unresolved string" case.)
  - [x] `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` (rev7 H1 — tightened predicate rejects prefixed-substring lookalikes): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and a stringified `id: "NotNodeID[int]"` annotation (where `NotNodeID` is not imported and not Strawberry's `NodeID`; the prefix means the string DOES contain `"NodeID["` as a substring but is NOT a token-shaped NodeID reference). Assert `ConfigurationError` raised at class-creation time with message containing both `"relay.NodeID"` and `"GlobalID"`. Worker 1 should also verify a `"MyNodeID[int]"` variant in the same test (parametrize or add a second assertion). Pins the rev7 H1 tightening: `_NODEID_STRING_RE = re.compile(r"(?:^|\.)NodeID\[")` requires a start-of-string or dot-boundary before `NodeID[`; the substring `NodeID[` inside `NotNodeID[` does not match. Without the regex tightening, the rev6 `"NodeID[" in raw` substring check would have accepted this false-positive and the consumer's typo would have slipped past the package guard.
  - [x] `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` (rev3 H1 escape-hatch acceptance): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an `id: relay.NodeID[int]` consumer annotation. Assert no `ConfigurationError` at class-creation time; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(...)` builds. Pins that the guard does NOT reject the advertised escape hatch. Mirrors the existing `tests/types/test_relay_interfaces.py:240`'s `test_composite_pk_with_explicit_node_id_annotation_is_accepted` pattern, but applies to a plain (non-composite-pk) Relay-Node-shaped type to specifically exercise this card's guard.
  - [x] `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` (rev4 H1 string-annotation acceptance; rev6 L3 — explicit string annotation is the default; rev7 H1 — renamed/split for resolved end-to-end contract): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an explicit stringified `id: "relay.NodeID[int]"` consumer annotation, **with `relay` imported at module scope** so the string resolves cleanly under both `typing.get_type_hints(cls, include_extras=True)` (the package's guard) AND Strawberry's downstream schema-construction resolution. Assert no `ConfigurationError` at class-creation time; assert `finalize_django_types()` succeeds; assert `strawberry.Schema(...)` builds; assert the introspected `id` field is `ID!` (the Relay-supplied interface field). Pins that the `typing.get_type_hints(cls, include_extras=True)` detection helper resolves stringified annotations correctly **and** Strawberry's downstream pipeline accepts the same string. This is the resolved-string end-to-end contract.
  - [x] `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` (rev7 H1 — fail-soft sub-case-1 split; rev8 M2 — precise recipe): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)` and an explicit stringified `id: "relay.NodeID[int]"` consumer annotation, **with `relay` NOT importable** from the class's resolution scope. Assert ONLY that class creation succeeds — no `ConfigurationError` at `__init_subclass__` time — because the fail-soft branch matches the `(?:^|\.)NodeID\[` regex on the raw string and suppresses the guard. **Do NOT assert** `finalize_django_types()` or `strawberry.Schema(...)` succeed; Strawberry's downstream resolution operates against the same module globals and will fail with its own error if the consumer has not made `relay` resolvable. The spec contract for this case is "package guard suppressed at class-creation time"; full end-to-end resolution is the consumer's responsibility. **Rev8 M2 — mandatory test recipe** (rev7's "Worker 1 picks during planning" with `types.ModuleType` / `TYPE_CHECKING` options dropped because (a) `TYPE_CHECKING` does not produce an unresolved-module-scope condition — the consumer's real module still exposes `relay` at import time — and (b) the load-bearing detail that `typing.get_type_hints(cls, include_extras=True)` resolves string annotations through `sys.modules[cls.__module__].__dict__` was elided, so the option-(a) sketch could silently false-pass by exercising the resolved-string path in the real test module): (1) generate a unique synthetic module name via `_stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"`; (2) register `sys.modules[_stub_name] = types.ModuleType(_stub_name)` and **assert** the stub module's `__dict__` has no `"relay"` key (this is what the fail-soft branch keys off — `typing.get_type_hints` raises `NameError` because `relay` is unresolvable in the class's module globals); (3) build the `DjangoType` via `types.new_class(name="UnresolvedRelayChild", bases=(DjangoType,), exec_body=_body)` where `_body` is a callable that mutates the class namespace dict to set `__module__ = _stub_name`, `__annotations__ = {"id": "relay.NodeID[int]"}`, and assigns a `Meta` class with `model = Category` and `interfaces = (relay.Node,)`; (4) assert ONLY that `types.new_class(...)` returns without raising — no `ConfigurationError`; **do NOT** call `finalize_django_types()` or build a `strawberry.Schema(...)`, since Strawberry's downstream resolution would re-trigger the unresolvable `relay` lookup against the same module globals; (5) wrap the entire body in `try/finally` (or use a pytest fixture with teardown) so **both** `sys.modules.pop(_stub_name, None)` **and** `registry.clear()` run even if the assertion fails — leaving stale synthetic modules in `sys.modules` would leak across tests, AND the synthesized DjangoType registers against `Category` in the package registry the moment class creation passes the guard (rev9 L1: even though the test only asserts class-creation success, the side effect is that `Category` now has an extra co-resident type that could poison the rev6 L2 cross-type cache test if it runs later in the same session). The repo's standard autouse `registry.clear()` fixture pattern handles this if Worker 1 lands the test in a file that already uses it; if not, the M2 recipe must wire it explicitly. **Without this recipe**, the test can silently run in the real test module where `relay` IS imported, exercise the resolved-string end-to-end path, and false-pass while pinning nothing about the fail-soft branch.
  - [x] `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` (rev6 H1 — fail-soft H1-sub-case-2 acceptance): declare a `DjangoType` with `Meta.interfaces = (relay.Node,)`, a directly-resolved `id: relay.NodeID[int]` consumer annotation, AND a forward-referenced sibling annotation like `items: list["AdminItemType"]` (or any annotation that doesn't resolve at class-creation time). Assert no `ConfigurationError` at class-creation time. Pins the rev6 H1 fix: when `typing.get_type_hints(cls, include_extras=True)` raises `NameError` because of the sibling annotation, the helper's fail-soft branch sees `cls.__annotations__["id"]` is an already-resolved `Annotated[int, NodeIDPrivate]` object (not a string), falls back to `_has_node_id_marker(raw)`, recognizes the marker, and accepts. Without this test, the rev5 fail-soft logic would silently false-positive-reject `id: relay.NodeID[int]` whenever any other annotation on the class fails to resolve — a realistic pattern for `DjangoType`s with forward-referenced relation annotations.
  - [x] `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` (rev3 H1 custom-pk acceptance; rev6 L3 — `description: int` recipe is the default): declare a `DjangoType` on a Relay-Node-shaped type with a non-`id` consumer scalar override (use **`description: int` as the recipe**; the monkeypatched `code = models.CharField(primary_key=True)` alternative is no longer recommended because it requires a fixture monkeypatch for marginal value). Assert no `ConfigurationError` is raised. Pins that the guard is keyed off the GraphQL field name `"id"`, not the model's pk name — a consumer who overrides a non-`id` field on a Relay-Node-shaped type does not collide with `Node.id` and must not be rejected.
  - [x] `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` (rev6 L1 + rev7 M1 — inverted contract: schema construction succeeds, not raises): declare a base `DjangoType` subclass `BaseWithId` with `id: int` annotation but no `Meta` (so `__init_subclass__` short-circuits the collection pipeline for the base). Then declare a child `ChildRelayType(BaseWithId)` with `class Meta: model = M; interfaces = (relay.Node,)`. Assert: (a) no `ConfigurationError` at class-creation time — the rev6 L1 guard predicate `"id" in cls.__annotations__` is False for the child (inherited annotations don't land in the subclass's own `__annotations__` dict); (b) **`strawberry.Schema(query=Query, types=[ChildRelayType])` SUCCEEDS** (rev7 M1 — this inverts the rev6 contract). `_build_annotations`'s `suppress_pk_annotation and field.name == pk_name` branch at `types/base.py:651-657` (pre-Slice-1) suppresses the synthesized scalar `id` annotation for the child, and the post-merge line at `types/base.py:138` (pre-Slice-1) replaces the child's `__annotations__` with `{**synthesized, **consumer_annotations}` — which contains neither the inherited `id: int` nor a synthesized one. Strawberry's `@strawberry.type` reads the child's assigned `__annotations__` and sees no `id`, applies Relay's `id: GlobalID!`, and `resolve_id_attr()` falls back to `"pk"`; (c) the introspected `id` field type is `ID!` (the Relay-supplied interface field), not `Int!`; (d) optionally, `ChildRelayType.resolve_id_attr() == "pk"`. Pins the corrected inheritance behavior — the H1 guard does NOT walk the MRO (rev6 L1 framing was correct on this point) but **pk-suppression in `_build_annotations` silently handles the inherited `id: int` case**, so Strawberry's `ValueError` does NOT fire (rev6 L1's downstream-failure claim was wrong; rev7 M1 corrects it). Without this test, future changes to the pk-suppression branch could regress the inherited-`id` corner without surfacing.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — added module-level imports (`re`, `typing`, `Annotated`, `NodeIDPrivate`); added three module-scope helpers (`_NODEID_STRING_RE`, `_has_node_id_marker`, `_id_annotation_is_relay_node_id`) above `class DjangoType`; collected `consumer_annotated_scalar_fields` parallel to the relation collection; unioned it into `consumer_authored_fields`; planted the H1 Relay collision guard between collection and `_build_annotations`; plumbed the new set through `DjangoTypeDefinition(...)` at the registration call. No edit to `_build_annotations`'s body.
- `django_strawberry_framework/types/definition.py` — added `consumer_annotated_scalar_fields: frozenset[str] = frozenset()` between `consumer_annotated_relation_fields` and `consumer_assigned_relation_fields` (grouped-by-style order per Decision 3 sample). Removed the inline Slice 1 TODO comment block.
- `pyproject.toml` — removed the temporary `[tool.ruff.lint.per-file-ignores]` entries (and the preceding 4-line comment) that scoped `ERA001` to `types/base.py` and `types/definition.py`, per spec rev10 L2 — atomic with the TODO body replacement in the two files.
- `tests/types/test_definition_order.py` — added new imports (`sys`, `types`, `uuid`, `django.db.models`, `strawberry.relay`, `_build_annotations`); added `_FakeUnsupportedField` fixture at the top of the file; replaced the Slice 1 TODO block with 18 new test functions (4 core override + 4 converter-bypass + 10 of the 11 Relay collision tests, with the 11th being the `direct_relay_node_subclass` reject test). The cluster lands between `test_assigned_scalar_field_override_keeps_consumer_resolver` and `test_scalar_field_class_attribute_shadowing_raises`.
- `tests/types/test_converters.py` — replaced the rev6 L3 TODO block with `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` beside the existing nested-`ArrayField` rejection test. The model field name and consumer-annotation name both use `arr` per rev4 L2.

### Tests added or updated

- `tests/types/test_definition_order.py::test_annotation_only_scalar_field_override_wins_over_synthesized` — pins consumer `description: int` survives `__init_subclass__` merge and finalize; Strawberry field type matches consumer annotation.
- `tests/types/test_definition_order.py::test_annotation_only_scalar_override_populates_definition_metadata` — pins new `consumer_annotated_scalar_fields` introspection set on `DjangoTypeDefinition`; pins union into `consumer_authored_fields`.
- `tests/types/test_definition_order.py::test_annotation_only_scalar_override_does_not_emit_synthesized_annotation` — pins the short-circuit fires: `_build_annotations`'s synthesized dict does NOT contain the overridden field name.
- `tests/types/test_definition_order.py::test_annotation_only_scalar_override_survives_strawberry_finalization` — pins end-to-end: GraphQL schema introspection shows the consumer's `Int!` for the overridden field.
- `tests/types/test_definition_order.py::test_annotation_override_of_unsupported_scalar_field_type_is_allowed` — pins `convert_scalar`'s unsupported-field-type rejection is bypassed when the consumer overrides; the baseline failure path is exercised in the same test body.
- `tests/types/test_definition_order.py::test_annotation_override_of_grouped_choices_field_is_allowed` — pins `convert_choices_to_enum` grouped-choices rejection is bypassed; `registry.get_enum(model, "status")` returns None on the overridden field.
- `tests/types/test_definition_order.py::test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` — pins the cross-type cache contract: the non-overriding co-resident populates the cache, the overriding type uses the consumer's annotation, and the cache entry is not leaked into the overriding type's GraphQL surface.
- `tests/types/test_definition_order.py::test_consumer_id_annotation_on_relay_node_type_raises` — pins the H1 guard's annotation-reject path on the `Meta.interfaces = (relay.Node,)` declaration shape; message contract pins both `"relay.NodeID"` and `"GlobalID"`.
- `tests/types/test_definition_order.py::test_consumer_id_annotation_on_direct_relay_node_subclass_raises` — pins the `issubclass(cls, relay.Node)` half of the guard's relay-shaped predicate (direct multi-inheritance shape with no `Meta.interfaces`).
- `tests/types/test_definition_order.py::test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises` — pins the H1 guard's assigned-reject path; error message contains all three keywords `"resolve_id"`, `"relay.NodeID"`, and one of `"display_id"`/`"sibling field"`.
- `tests/types/test_definition_order.py::test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` — pins the rev5 M1 / rev7 H1 narrow fail-soft contract: a typo like `id: "MissingType"` is rejected by the `(?:^|\.)NodeID\[` regex on the raw string.
- `tests/types/test_definition_order.py::test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` — pins the rev7 H1 tightening: `"NotNodeID[int]"` and `"MyNodeID[int]"` (both checked) are rejected because the regex requires a start-of-string or dot-boundary before `NodeID[`.
- `tests/types/test_definition_order.py::test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` — pins the direct-form escape hatch (`id: relay.NodeID[int]`) is accepted end-to-end.
- `tests/types/test_definition_order.py::test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` — pins the stringified-form escape hatch (`id: "relay.NodeID[int]"` with `relay` importable at module scope) succeeds end-to-end through finalize + schema build; the introspected `id` is `ID!`.
- `tests/types/test_definition_order.py::test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` — implements the rev8 M2 mandatory recipe (synthetic module via `types.ModuleType`, `types.new_class` with the stub module name, both `sys.modules` and `registry.clear()` cleanup in `finally`). Asserts only that class creation succeeds — the package guard suppression is the contract; downstream Strawberry resolution is the consumer's responsibility.
- `tests/types/test_definition_order.py::test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` — pins the rev6 H1 fail-soft sub-case-2 fix: `id: relay.NodeID[int]` paired with a forward-referenced sibling annotation (`items: list["AdminItemType"]`) is still accepted because the fail-soft branch inspects the resolved object via `_has_node_id_marker(raw)`.
- `tests/types/test_definition_order.py::test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` — pins the guard is keyed on the GraphQL field name `"id"`, not on the model's pk name; a `description: int` override on a Relay-Node-shaped type passes through unchanged.
- `tests/types/test_definition_order.py::test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` — pins the rev7 M1 inversion: the child's own `__annotations__` has no `"id"` key (inherited annotation doesn't land in the subclass dict), so the guard doesn't fire; `_build_annotations`'s pk-suppression branch silently drops the synthesized `id` for the Relay-Node-shaped child; `strawberry.Schema(types=[ChildRelayType])` succeeds and introspecting `id` returns `ID!`.
- `tests/types/test_converters.py::test_annotation_override_of_arrayfield_with_nested_array_is_allowed` — pins the nested-`ArrayField` shape-rejection bypass: a `_FakeArrayField(_FakeArrayField(IntegerField()))` model field paired with a consumer `arr: list[list[int]]` annotation finalizes cleanly; the override's annotation survives finalize. Beside the existing `test_array_field_multidim_rejected_via_fake_sentinel` reject test (the rejection path stays in force for non-overridden cases).

### Validation run

- `uv run ruff format .` — pass (1 file reformatted — `tests/types/test_definition_order.py` — which is the slice-intended file we'd just edited; the reformat is a consequence of our edit and stays in the diff).
- `uv run ruff check --fix .` — pass (no fixes applied; all checks passed).
- `git status --short` after both ruff invocations:
  - `M django_strawberry_framework/types/base.py` — slice-intended (collection, helpers, guard, plumbing).
  - `M django_strawberry_framework/types/definition.py` — slice-intended (new field).
  - `M pyproject.toml` — slice-intended (per-file-ignores removal per rev10 L2).
  - `M tests/types/test_converters.py` — slice-intended (`ArrayField` bypass test).
  - `M tests/types/test_definition_order.py` — slice-intended (18 Slice 1 tests + `_FakeUnsupportedField` fixture + new imports).
  - `?? docs/builder/bld-slice-1-annotation_scalar_overrides.md` — slice-intended (this artifact; Worker 1 wrote the plan, Worker 2 appends the build report below).
  - `?? docs/builder/build-015-consumer_overrides_scalar-0_0_6.md` — slice-intended (Worker 0's build plan; pre-existing untracked).
- Focused tests run, all passing without `--cov*` flags:
  - `uv run pytest tests/types/test_definition_order.py --no-cov -x` — 34 passed (18 new + 16 pre-existing).
  - `uv run pytest tests/types/test_converters.py::test_annotation_override_of_arrayfield_with_nested_array_is_allowed tests/types/test_converters.py::test_array_field_multidim_rejected_via_fake_sentinel --no-cov -x` — 2 passed (new bypass test + existing reject test confirm coexistence).
- Final `uv run ruff format --check .` and `uv run ruff check .` both pass.

### Implementation notes

- **Inline-introspection over `_introspect_field_type` reuse.** The end-to-end test (`test_annotation_only_scalar_override_survives_strawberry_finalization`) and the resolved-string Relay test inline the introspection query rather than cross-importing the converter-host helper. This matches Worker 1's planning preference; either path produced an equivalent contract.
- **Explicit assignment form for the assigned-`id` reject test.** Used `id = strawberry.field(resolver=lambda root: "x")` rather than the `@strawberry.field` decorator form. Both shapes trip `isinstance(cls.__dict__.get("id"), StrawberryField)` identically; the assignment form is more directly readable about which path is under test.
- **Two-attempt parametrization of the typo-lookalike test.** `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` exercises both `"NotNodeID[int]"` and `"MyNodeID[int]"` in the same test body by calling `registry.clear()` between the two attempts (the autouse fixture clears only at entry/exit, not between sub-blocks). Worker 1's planning note allowed parametrization OR a second assertion in the same test; the in-body second attempt keeps the test self-contained without adding a pytest parametrize import.
- **Cross-type cache test uses GraphQL aliases.** The two-type introspection in `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` uses a single query with two `__type(name: ...)` calls aliased via `__overrideTwo: __type(name: "NonOverrideType")`. Pulling both type metadata bodies in one query is simpler than two `execute_sync` calls.
- **`assert NestedArrayOverrideOwnerType.__annotations__["arr"] == list[list[int]]` is the verification assertion for the ArrayField bypass test.** The test recipe in the plan said "assert no error is raised and `finalize_django_types()` succeeds"; landing an explicit annotation check anchors what the override actually achieved (otherwise the test would pass even if a future refactor lost the consumer annotation).
- **`models.Field` used for `_FakeUnsupportedField`** — a bare subclass with no `__init__` or class body satisfies the "MRO has no `SCALAR_MAP` match" requirement; no extra surface needed.
- **The `relay.Node` direct-inheritance test uses `class DirectRelayChild(DjangoType, relay.Node)`** — multiple inheritance is the documented way to declare a relay-node-shaped `DjangoType` without a `Meta.interfaces` tuple. The H1 guard's `issubclass(cls, relay.Node)` disjunct fires on this shape.

### Notes for Worker 3

- The plan's step 7 noted the `consumer_assigned_*` lines on `DjangoTypeDefinition` were already in the correct grouped-by-style position (between the annotated-* and assigned-* groups becomes coherent once the new field lands in the gap); no cosmetic re-order was needed and none was performed.
- The `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` test creates a class via `types.new_class("UnresolvedRelayChild", (DjangoType,), {}, _body)` so the autouse `registry.clear()` fixture between tests is augmented by an explicit `registry.clear()` inside the test's `finally` block. This is intentional per rev9 L1 and is exercised by the test passing alongside `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` (which is sensitive to stale `Category` registrations).
- The bare `class CategoryNode(DjangoType): id: int; class Meta: ...; interfaces = (relay.Node,)` test patterns in the reject cluster all trip the H1 guard at class-creation time. `pytest.raises` captures `ConfigurationError` and the message-keyword assertions hold against the implemented error strings.
- No shadow files were used during this implementation; the slice was small enough to read directly. The plan's line-number hints were accurate after my edits shifted them slightly (the helpers added ~60 lines above `class DjangoType`, the guard removed ~80 lines of TODO comments while adding ~25 lines of real code).
- The `__overrideTwo: __type(...)` GraphQL alias in the cross-type cache test is GraphQL-spec-compliant (a top-level `__type` query field can be aliased like any other field) — the spec test passes cleanly.

### Notes for Worker 1 (spec reconciliation)

No spec gaps surfaced. The spec rev10 cluster (the 19-test contract, the H1 guard with the rev7 token regex, the rev8 M1 helper structure, and the rev8 M2 unresolved-string recipe) translated mechanically to working code without architectural drift. The plan's step 7 already noted that the current `definition.py` field order is in the grouped-by-style shape post-insertion (no extra cosmetic re-order needed) — which is what we observed.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### Inline-model `Meta.managed = False` consistency

The four inline `models.Model` declarations introduced in `tests/types/test_definition_order.py` (`UnsupportedFieldOwner` at `:430`, `GroupedChoiceOwner` at `:459`, `CoResidentChoiceOwner` at `:482`) set `app_label` only, without `managed = False`. The sibling `_FakeArrayField` test pattern in `tests/types/test_converters.py` (e.g. `:483-488`, `:917-921`, `:992-996`) consistently sets `managed = False` alongside `app_label`. Tests pass either way under the test runner, but the inline-model convention used everywhere else in the test trees is `managed = False`. Worker 2 may align with the existing convention in a future slice, but this is a stylistic-only note (no functional difference under `pytest` because Django's test runner does not migrate test-only models).

```tests/types/test_definition_order.py:430:434
    class UnsupportedFieldOwner(models.Model):
        myfield = _FakeUnsupportedField()

        class Meta:
            app_label = "test_spec015_unsupported"
```

### DRY findings

- **Relay-shaped predicate duplicated at two call sites.** The expression `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` lives at `django_strawberry_framework/types/base.py:173` (the new H1 guard) and `django_strawberry_framework/types/base.py:708` (the pre-existing `suppress_pk_annotation` in `_build_annotations`). Worker 1's plan (artifact `### DRY analysis` bullet, "Duplication risk avoided") explicitly chose to NOT extract a `_is_relay_shaped(cls, interfaces)` helper for this slice on the grounds that the two sites have different timing (class-creation vs. annotation synthesis) and that a single-extracted-helper for two sites is premature. Worker 1 left a follow-up note for the integration pass to revisit. Recording this here so Worker 1 has the explicit duplication citation ready when the integration pass runs.
- **Error-message keyword overlap is intentional contract pinning, not DRY drift.** The strings `"relay.NodeID"`, `"GlobalID"`, and `"remove relay.Node from Meta.interfaces"` appear in both the assigned-side error message (`base.py:178-190`) and the annotation-side error message (`base.py:192-198`), and the test assertions at `tests/types/test_definition_order.py:555-556`, `:571-572`, `:606-607`, `:623-624`, `:639-640` walk these keywords explicitly. The two error messages are distinct human-readable strings with different call-to-action lists; the keyword overlap is the spec contract (per [Decision 7](../spec-015-consumer_overrides_scalar-0_0_6.md) and the Slice 1 checklist's three-keyword pin). No consolidation warranted.
- **Repeated string literal `"relay.NodeID"` (6x) and `"GlobalID"` (5x) in `tests/types/test_definition_order.py`.** Surfaced by the static inspection helper's repeated-string-literals section. These are the spec-required keyword assertions across the 5 Relay-collision reject tests; consolidating them into a module-level constant tuple would obscure the per-test contract documentation. No action recommended.
- **Repeated test pattern: introspection-query wrapper.** Four tests (`test_annotation_only_scalar_override_survives_strawberry_finalization` at `:394`, `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types` at `:479`, `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end` at `:665`, and `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` at `:749`) inline a near-identical `__type(name: "<TypeName>") { fields { name type { kind name ofType { kind name } } } }` introspection query and the same `{f["name"]: f["type"] for f in ...}` walk. Worker 1's plan explicitly chose inline-introspection over the `_introspect_field_type` helper in `tests/types/test_converters.py:434` (cross-file dependency cost). The duplication stays inside one test file and the bodies are short enough to read; a `_introspect_field_type_for_definition_order(...)` helper would be an overlapping responsibility with the converter-host helper. Recommend leaving as-is; flagging for the integration pass to consider whether a shared `_introspect_field_type` lives somewhere mutually accessible to both test files (e.g. `tests/types/conftest.py`).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns no output. `__all__` is unchanged (`BigInt`, `DjangoOptimizerExtension`, `DjangoType`, `OptimizerHint`, `__version__`, `auto`, `finalize_django_types`). The slice ships no new public exports, matching the spec Definition of done.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- The three module-scope helpers (`_NODEID_STRING_RE`, `_has_node_id_marker`, `_id_annotation_is_relay_node_id`) are tightly scoped, well-docstringed, and mechanically transcribe the spec's pseudocode block. The success path correctly lives inside the helper's try-block after the except clause (rev8 M1).
- The H1 guard placement at `base.py:173-198` lands between the four `consumer_*_fields` collection and the `_build_annotations` invocation — exactly where spec Decision 7 pinned it, with all inputs already in hand.
- The four `consumer_*_fields` introspection sets on `DjangoTypeDefinition` are in the grouped-by-style order (annotated-relation, annotated-scalar, assigned-relation, assigned-scalar) per spec L1 fix.
- The `consumer_authored_fields` union splat (`base.py:165-172`) keeps the four sets disjoint inputs with no collapse into a tagged-union dict — matches spec Decision 6 ("four separate frozensets on `DjangoTypeDefinition`, not collapsed").
- The 18 tests in `test_definition_order.py` plus the 1 test in `test_converters.py` account for the 19-test contract pinned at spec `:744`.
- The `_FakeUnsupportedField` baseline path (`tests/types/test_definition_order.py:436-442`) explicitly exercises the "without override fails" half so the bypass-is-relative-to-baseline contract is documented in-test.
- The `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` test correctly implements the rev8 M2 mandatory recipe: `uuid`-suffixed stub module name, registers in `sys.modules`, asserts `"relay"` is not in the stub's `__dict__`, uses `types.new_class(..., exec_body=_body)` with `__module__` set to the stub, and runs both `sys.modules.pop(stub_name, None)` and `registry.clear()` in the `finally` block (rev9 L1 + rev10 M2). The test passes against the actual implementation.
- The `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression` test correctly exercises the rev7 M1 inverted contract — pk-suppression handles the inherited annotation silently and Strawberry's interface-supplied `id: GlobalID!` lands cleanly.
- The temporary `[tool.ruff.lint.per-file-ignores]` entries (4-line comment + 2 per-file-ignore lines) removed atomically with the TODO body replacement, per spec rev10 L2. `uv run ruff check .` passes cleanly post-Slice-1.
- All 635 package tests pass; the focused run on `tests/types/test_definition_order.py` shows 34 of 34 passing (18 new + 16 pre-existing).
- The error messages are precise about the supported workarounds. Assigned-side message names all three alternatives (`resolve_id`, `relay.NodeID[<pk_type>]`, resolver-backed sibling field). Annotation-side message names the escape hatch (`relay.NodeID[<pk_type>]`) and explains the interface contract (`Relay interface supplies id: GlobalID!`).

### Temp test verification

No temp tests created. The implementation matched the plan and the spec contracts cleanly; the existing tests in `tests/types/test_definition_order.py` and `tests/types/test_converters.py` cover every spec checklist item. Disposition: N/A.

### Notes for Worker 1 (spec reconciliation)

- **Cross-slice DRY follow-up for the relay-shaped predicate.** Worker 1's plan explicitly deferred extraction of `_is_relay_shaped(cls, interfaces)` to the integration pass. The two call sites (`base.py:173` and `base.py:708`) carry the identical predicate `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`. Integration-pass candidate: hoist to a module-level helper next to `_has_node_id_marker` / `_id_annotation_is_relay_node_id`. Risk: low — the predicate is a single line and well-localized.
- **Introspection-query helper across test files (optional integration-pass follow-up).** `_introspect_field_type` at `tests/types/test_converters.py:434` and the four near-copies in `tests/types/test_definition_order.py` are an integration-pass candidate for promotion to `tests/types/conftest.py` (or similar shared test infrastructure). Worker 1 has noted Worker 1's planning preference for inline-introspection over cross-importing; this is a follow-up suggestion only.
- **Spec is internally consistent post-Slice-1.** No spec edits required from this slice. The 19-test contract, the rev8 M1 helper structure, and the rev8 M2 unresolved-string recipe all translated to working code mechanically.

### Review outcome

`review-accepted`

---

## Final verification (Worker 1)

- **Spec slice checklist** — pass. Every `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` is now `- [x]`. The four top-level items (collection, definition field, union, plumbing) plus the module-scope helpers cluster (3 sub-boxes), the H1 Relay collision guard, and the test cluster (4 core + 4 converter-bypass + 11 Relay-collision = 19 sub-boxes) all landed in the diff and were verified against source (`types/base.py:72-126` for the helpers, `:158-160` for the new collection, `:165-172` for the union, `:173-198` for the guard, `:220` for the plumbing; `types/definition.py:30` for the new field; `tests/types/test_definition_order.py` for 18 tests + `_FakeUnsupportedField` fixture; `tests/types/test_converters.py:1040` for the ArrayField bypass test).
- **DRY check across this slice and prior accepted slices** — pass. This is the first slice in the build; the only prior context is the pre-build codebase. Worker 3 identified two integration-pass candidates: (a) the relay-shaped predicate `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` is duplicated at `types/base.py:173` (new H1 guard) and `types/base.py:708` (pre-existing `_build_annotations` pk-suppression branch); (b) the inline introspection-query wrapper is repeated across four tests in `test_definition_order.py` and overlaps with `_introspect_field_type` at `tests/types/test_converters.py:434`. Worker 1's plan explicitly deferred extraction of `_is_relay_shaped(...)` to the integration pass on the grounds that the two sites have legitimately different timing (class-creation vs. annotation synthesis) and a single-helper-for-two-call-sites extraction is premature. Worker 3 concurred and recorded both as integration-pass follow-ups. I accept both deferrals — they are explicit notes for `bld-integration.md`, not silent omissions, and the slice contract is internally clean. Two other potential DRY signals (repeated error-message keywords and `relay.NodeID`/`GlobalID` string literals across reject tests) are intentional spec-pinned contracts per Worker 3's analysis — no action.
- **Existing tests still pass — focused scope** — pass. Ran `uv run pytest tests/types/test_definition_order.py tests/types/test_converters.py tests/types/test_base.py --no-cov -q`. Result: 146 passed, 3 skipped (the 3 pre-existing skips include the Slice 2 candidate at `tests/types/test_base.py:444-465` which will be deleted in Slice 2 per spec; the other two are pre-existing). No `--cov*` flags used. No coverage inspection performed.
- **Spec reconciliation** — no edits needed. Worker 2's `### Notes for Worker 1 (spec reconciliation)` reports "No spec gaps surfaced. The spec rev10 cluster... translated mechanically to working code without architectural drift." Worker 3's `### Notes for Worker 1 (spec reconciliation)` reports "Spec is internally consistent post-Slice-1. No spec edits required from this slice." I verified the spec status-line at `docs/spec-015-consumer_overrides_scalar-0_0_6.md:4` ("Status: draft (revision 10, post-rev9 review)") still accurately describes the spec's state — Slice 1 is the first of five slices and four remain unstarted, so the draft framing is correct.
- **Final status** — `final-accepted`.

### Summary

Slice 1 closes the consumer override symmetry gap for scalar fields. `DjangoType.__init_subclass__` now collects a `consumer_annotated_scalar_fields` frozenset parallel to the existing `consumer_annotated_relation_fields`, unions it into `consumer_authored_fields`, and plumbs it through to `DjangoTypeDefinition` — completing the four-corner override matrix (relation × annotation, relation × assigned, scalar × annotation, scalar × assigned). The slice also lands the H1 Relay `id` collision guard at `__init_subclass__` time, replacing the downstream Strawberry-side `ValueError` with a package-owned `ConfigurationError` that points consumers at the `relay.NodeID[<pk_type>]` escape hatch (annotation-side) or `@classmethod resolve_id` / resolver-backed sibling field (assigned-side). The guard uses three module-scope helpers (`_NODEID_STRING_RE`, `_has_node_id_marker`, `_id_annotation_is_relay_node_id`) with a careful two-branch fail-soft path for unresolved forward references. The `consumer_authored_fields` short-circuit at `_build_annotations:644` (unchanged body) drops both annotation synthesis AND every `convert_scalar` validation / side effect (unsupported-field-type rejection, grouped-choices rejection, `ArrayField` shape rejection, choice-enum cache registration) for the overridden field — the consumer's annotation is authoritative. 19 new tests (18 in `tests/types/test_definition_order.py` + 1 in `tests/types/test_converters.py`) pin the core override behavior, the four converter-bypass regressions, and the eleven Relay-collision sub-contracts (5 reject + 6 accept). The temporary `ERA001` per-file-ignores in `pyproject.toml` (added pre-Slice-1 to quiet TODO pseudocode lint failures) were removed atomically with the TODO body replacements.

### Spec changes made (Worker 1 only)

None.

---

## Maintainer-feedback revision plan (Worker 1)

Source: `docs/feedback.md` (Implementation review — spec-015 consumer scalar overrides, Slice 1). The maintainer ran a full coverage-aware test pass externally after the build cycle's nominal close. Two findings were recorded; both route through the Slice 1 loop per BUILD.md "Final test-run gate" failure-handling ("If failures appear, record them in `bld-final.md`, then re-loop through whichever slice owns the failing behavior"). This section authorizes the Worker 2 apply-changes pass and the Worker 3 re-review pass; the artifact's top-level `Status:` is set to `revision-needed` accordingly.

### M1 — `_id_annotation_is_relay_node_id`'s `id_hint is None` branch is unreachable and blocks 100% coverage

**Feedback verbatim (`docs/feedback.md` M1):**

Reference: `django_strawberry_framework/types/base.py:123-125`.

```python
id_hint = hints.get("id")
if id_hint is None:
    return False          # line 125 — never executed
return _has_node_id_marker(id_hint)
```

The full-suite coverage run shows exactly one uncovered line in the package: `base.py:125`. The call site at `base.py:205` reads `if has_id_annotation and not _id_annotation_is_relay_node_id(cls):` where `has_id_annotation = "id" in cls.__annotations__`. By the time `_id_annotation_is_relay_node_id(cls)` is called, `"id"` is guaranteed to be in `cls.__annotations__`, so `typing.get_type_hints(cls, include_extras=True)` resolves `id` and `hints.get("id")` returns a non-`None` value. The defensive `if id_hint is None: return False` is dead code under the current call-site precondition. The reviewer's preferred resolution: REMOVE the redundant check entirely and call `return _has_node_id_marker(hints.get("id"))` directly — `_has_node_id_marker(None)` already returns False safely because `typing.get_origin(None)` is `None`, not `Annotated`, so the conjunction short-circuits.

**Planned resolution.** REMOVE lines 123-125 of `django_strawberry_framework/types/base.py` (the `id_hint = hints.get("id"); if id_hint is None: return False; return _has_node_id_marker(id_hint)` block) and replace with the single line `return _has_node_id_marker(hints.get("id"))`. Rationale: (a) the defensive guard is unreachable under the sole call site's precondition (`has_id_annotation = "id" in cls.__annotations__` is True at `base.py:205`); (b) `_has_node_id_marker(None)` already returns False safely under the lazy-evaluation conjunction in its body, so the explicit `None` check carries no behavior; (c) the dead line blocks the Definition of done's DoD #4 ("`uv run pytest` passes locally with 100% package coverage" — `pyproject.toml [tool.coverage.report] fail_under = 100`). Reviewer's preferred option of three (REMOVE > `# pragma: no cover` > contrive-a-test) is adopted because it leaves the helper at its leanest faithful shape rather than papering over the dead code with a coverage exclusion or a synthetic test.

Post-change body (verbatim target shape):

```python
def _id_annotation_is_relay_node_id(cls: type) -> bool:
    # ... unchanged docstring ...
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
    except (NameError, AttributeError):
        raw = cls.__annotations__.get("id")
        if isinstance(raw, str):
            return bool(_NODEID_STRING_RE.search(raw))
        return _has_node_id_marker(raw)
    return _has_node_id_marker(hints.get("id"))
```

Three lines removed (the `id_hint =` assignment, the `if id_hint is None:` line, and the `return False` line); one line added (`return _has_node_id_marker(hints.get("id"))`). Net: -2 lines.

**Test impact.** None. The existing 19-test Slice 1 cluster already pins every observable contract:

- The resolved-success path (NodeID marker present) is hit by `test_consumer_id_relay_nodeid_annotation_on_relay_node_type_is_accepted` and `test_consumer_id_resolved_string_relay_nodeid_annotation_on_relay_node_type_is_accepted_end_to_end`.
- The resolved-reject path (non-NodeID type) is hit by `test_consumer_id_annotation_on_relay_node_type_raises`.
- The fail-soft sub-case-1 paths (id-itself-unresolved-string) are hit by `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` (accept) and `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` + `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` (reject).
- The fail-soft sub-case-2 path (id-resolved-but-sibling-failed) is hit by `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`.

The branch being removed is reachable in source today but unreachable from the call graph; removing it preserves every assertion shape verbatim because the new direct delegate has the same return value at every input the call site can ever pass. No new test is justified (per the reviewer: "I cannot construct a realistic call shape that produces that divergence, so this option [contrive a test] is least attractive").

### L1 — `registry.clear()` between assertions in the typo-lookalike test is unnecessary

**Feedback verbatim (`docs/feedback.md` L1):**

Reference: `tests/types/test_definition_order.py:610-640`.

`test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` declares two classes (`CategoryNodeNot` with `id: "NotNodeID[int]"`, then `CategoryNodeMy` with `id: "MyNodeID[int]"`) in sequence, both inside `pytest.raises(ConfigurationError)` blocks, with an explicit `registry.clear()` at line 626 between them. The H1 guard raises at `base.py:206` **before** `base.py:240`'s `registry.register_with_definition(...)` call. Neither class registers with the registry, so there is no state to clear between the two `pytest.raises` blocks. The `_isolate_registry` autouse fixture at `tests/types/test_definition_order.py:29` handles per-test cleanup. Not a bug — harmless defensive code, no test-correctness impact. Reviewer is neutral.

**Planned resolution.** DROP the `registry.clear()` call at `tests/types/test_definition_order.py:626` (one-line deletion plus the adjacent blank line if pre-existing; net -1 or -2 lines depending on surrounding whitespace). Worker 1's decision rationale: (a) the H1 guard raises BEFORE `registry.register_with_definition` per Decision 7's contract ("the guard fires before registry mutation"), so neither class registers and there is no inter-assertion state to clear; (b) the `_isolate_registry` autouse fixture (`tests/types/test_definition_order.py:29`) handles real per-test cleanup, so the inline `registry.clear()` would only matter if `pytest.raises` semantics could leak state between assertions inside a single test — which they cannot; (c) dropping the call makes the test body match the spec's contract (the guard fires before mutation) rather than reading as belt-and-suspenders cleanup against a failure mode that cannot occur; (d) reducing test-body noise marginally helps the reader. Reviewer is neutral ("harmless either way"), and the decision tips on the spec-contract-alignment principle rather than a behavior gain.

**Test impact.** None functionally. The two `pytest.raises(ConfigurationError)` blocks each pin their own class-creation failure independently; removing the `registry.clear()` between them does not alter which exceptions fire or which assertion messages are tested. After the edit, `_isolate_registry` is the sole cleanup mechanism for this test (matching every other test in the file).

### Spec changes made (Worker 1 only)

Two edits to `docs/spec-015-consumer_overrides_scalar-0_0_6.md` in this revision pass:

1. **`docs/spec-015-consumer_overrides_scalar-0_0_6.md:4`** — status line updated from `Status: draft (revision 10, post-rev9 review).` to `Status: draft (revision 11, post-build maintainer-feedback pass).` so the header reflects the new revision. Reason: rev11 records the maintainer's post-close finding and the resulting pseudocode tightening; the status line must name the active revision to stay accurate per worker-1.md's "Spec status-line re-verification" rule.

2. **`docs/spec-015-consumer_overrides_scalar-0_0_6.md:654-657`** (Decision 7's pseudocode block, rev8 M1 entry's success path) — the three-line block

   ```python
   id_hint = hints.get("id")
   if id_hint is None:
       return False
   return _has_node_id_marker(id_hint)
   ```

   was replaced with the single line `return _has_node_id_marker(hints.get("id"))` plus an inline rev11 comment block above it explaining why the redundant guard was dropped (unreachable under the call site's `has_id_annotation = "id" in cls.__annotations__` precondition, redundant given `_has_node_id_marker(None)` already short-circuits safely, blocked the 100% coverage gate). Reason: align the spec's literal pseudocode with the post-revision implementation so future readers of Decision 7 see one shape, not two. Per Worker 1 role: option (b) — edit the spec to drop the redundant guard — over option (a) — keep the spec literal and `# pragma: no cover` the implementation — because the pseudocode was tightened, not relaxed; the new shape is strictly leaner and the rev11 inline comment preserves the rev8-vs-rev11 audit trail.

3. **`docs/spec-015-consumer_overrides_scalar-0_0_6.md` revision history** — appended a new `**Revision 11** (post-build maintainer-feedback pass) — one medium-severity dead-code fix surfaced by the maintainer's external coverage-aware test pass after the build cycle nominally closed; recorded in `docs/feedback.md` and routed back through the Slice 1 loop per BUILD.md "Final test-run gate" failure-handling:` block documenting the M1 fix and noting that the L1 nit is test-file-local and does not propagate into the spec body. Reason: the spec's revision history is the durable audit trail; appending rev11 keeps the chain unbroken.

L1 is intentionally NOT a spec edit. The `registry.clear()` placement is test-file local and the spec's "the guard fires before registry mutation" contract is unchanged by either keeping or dropping the call. Worker 2 applies the L1 edit to `tests/types/test_definition_order.py:626` directly; no Decision-level commitment moves.

### Build-plan checkbox

Worker 0 must also un-tick Slice 1's checkbox in `docs/builder/build-015-consumer_overrides_scalar-0_0_6.md:22` (currently `- [x]` per build-plan state on read; per the maintainer's framing in the revision-pass dispatch, Slice 1 and the two downstream gates — Integration and Final — are all un-ticked pending re-run). Worker 1 does not edit build-plan checkboxes; that step is Worker 0's responsibility on the next dispatch.

### What Worker 2 does next

Two atomic edits in one apply-changes pass:

1. `django_strawberry_framework/types/base.py:123-126` — replace the three-line success path with `return _has_node_id_marker(hints.get("id"))`. Drop the `id_hint =` assignment line and the `if id_hint is None: return False` two-liner.
2. `tests/types/test_definition_order.py:626` — drop the `registry.clear()` call (preserve the surrounding blank-line spacing as it would naturally fall after the deletion).

Then `uv run ruff format .` and `uv run ruff check --fix .` per AGENTS.md / START.md. No new tests required. No new imports required. The `# noqa` comments on the typo-lookalike test's `id: "NotNodeID[int]"` and `id: "MyNodeID[int]"` annotations stay unchanged.

### What Worker 3 does next (on re-review)

The re-review pass should confirm:

- Both atomic edits landed at the cited lines and nothing else changed in `types/base.py` or `tests/types/test_definition_order.py`.
- `_id_annotation_is_relay_node_id`'s success path now delegates directly to `_has_node_id_marker(hints.get("id"))` with no intermediate assignment or guard.
- The 19-test Slice 1 cluster runs unchanged (Worker 3 may run a focused `uv run pytest tests/types/test_definition_order.py tests/types/test_converters.py --no-cov -q` to confirm pass, without coverage flags per BUILD.md).
- No drift in `__init__.py` public exports (re-verify `git diff -- django_strawberry_framework/__init__.py` is empty for the apply-changes diff).
- The spec edits at `docs/spec-015-consumer_overrides_scalar-0_0_6.md:4`, `:654-657`, and the new Revision 11 history block are present and match the artifact's `### Spec changes made (Worker 1 only)` description verbatim.

No DRY scan is required — the apply-changes diff is two lines net.

### What Worker 1 does after Worker 3 accepts

A second `## Final verification (Worker 1, pass 2)` section is appended at the same top level (per BUILD.md "Re-pass sections"), the slice's `Status:` flips back to `final-accepted`, and Worker 0 re-ticks the Slice 1 checkbox in `docs/builder/build-015-consumer_overrides_scalar-0_0_6.md`. Then Worker 1 re-runs the final test-run gate (`docs/builder/bld-final.md`, regenerated or updated with a pass-2 section) — the gate's `uv run pytest --no-cov` must still report 707 passed / 2 skipped (or equivalent), and CI's coverage gate (`fail_under = 100`) is now satisfied because the dead line is gone.

### Blockers

None. The plan is mechanically applicable; both edits are line-local; no new fixtures, no new test models, no new imports, no public-surface changes. The integration-pass artifact and final-test-run-gate artifact will need pass-2 sections after this loop closes, but those are downstream of Worker 0's re-dispatch flow and not Worker 1's revision-plan responsibility here.

---

## Build report (Worker 2, pass 2)

### Files touched

- `django_strawberry_framework/types/base.py` — M1 fix: replaced the three-line block `id_hint = hints.get("id"); if id_hint is None: return False; return _has_node_id_marker(id_hint)` at lines 123-126 with the single line `return _has_node_id_marker(hints.get("id"))`. The defensive `id_hint is None` guard at line 125 was unreachable under the sole call site's precondition (`has_id_annotation = "id" in cls.__annotations__` at `base.py:205` is True before invocation, so `hints.get("id")` is non-None), and `_has_node_id_marker(None)` already returns False safely under its lazy-conjunction body. Net -2 lines.
- `tests/types/test_definition_order.py` — L1 fix: removed the `registry.clear()` call at line 626 (between the two `pytest.raises(ConfigurationError)` blocks in `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`). The H1 guard raises before `registry.register_with_definition`, so neither `CategoryNodeNot` nor `CategoryNodeMy` registers and there is no inter-assertion state to clear; the `_isolate_registry` autouse fixture handles real per-test cleanup. Removed the line and one adjacent blank line; net -2 lines.

### Tests added or updated

None. The revision is dead-code removal plus an unnecessary-call removal; no behavioral change, no new test contracts. The existing 19-test Slice 1 cluster already pins every observable contract for the M1 success path (per the revision plan's "Test impact" analysis), and the L1 edit removes a setup line, not an assertion.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged after the two edits).
- `uv run ruff check --fix .` — pass (All checks passed!).
- `git status --short` — Slice-1-revision-intended (2 files): `django_strawberry_framework/types/base.py` (status `MM` — Slice 1 carry-over now layered with this pass's M1 edit) and `tests/types/test_definition_order.py` (status `MM` — Slice 1 carry-over now layered with this pass's L1 edit). All other modified files in the working tree are carry-over from prior Slices 1-5 and Worker 1's revision-plan setup (CHANGELOG.md, KANBAN.md, TODAY.md, docs/GLOSSARY.md, docs/README.md, docs/builder/BUILD.md, docs/builder/bld-final.md, docs/builder/bld-integration.md, docs/builder/bld-slice-{2,3,4,5}-*.md, docs/builder/build-015-*.md, docs/builder/worker-0.md, docs/feedback.md, docs/spec-015-consumer_overrides_scalar-0_0_6.md, pyproject.toml, tests/types/test_base.py, tests/types/test_converters.py, django_strawberry_framework/types/definition.py); these are out of scope for the Slice 1 revision's classification per the dispatch contract.
- Focused pytest run: `uv run pytest tests/types/test_definition_order.py tests/types/test_relay_interfaces.py --no-cov -q` → 96 passed in 2.77s. No regression; the test count is unchanged (the L1 edit removed a single setup line, not an assertion).

### Implementation notes

- This pass 2 implements the maintainer-feedback revision plan exactly. No architectural decisions made. Worker 1's plan at lines 493-604 of this artifact specifies both edits verbatim (M1 at `base.py:123-126`, L1 at `tests/types/test_definition_order.py:626`); Worker 2 transcribes them mechanically. The line numbers on disk matched the plan exactly (re-verified via grep before each edit).
- The `Edit` tool's exact-string-match contract was the natural enforcement for the L1 edit: matching a six-line context window around the `registry.clear()` call disambiguated it from the other `registry.clear()` calls in the file (lines 32, 34, 714) without needing `replace_all`.

### Notes for Worker 3

- Both atomic edits landed at the cited lines and nothing else changed in `types/base.py` or `tests/types/test_definition_order.py`. Verify by reading the diff against HEAD — the M1 change is a 4-line-to-1-line replacement inside `_id_annotation_is_relay_node_id` after the `except (NameError, AttributeError):` clause; the L1 change is the removal of a single `registry.clear()` line plus its adjacent blank line between the two `pytest.raises` blocks in `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises`.
- Verify the focused test count is unchanged (96 in `tests/types/test_definition_order.py` + `tests/types/test_relay_interfaces.py`). The L1 edit removes a setup line, not an assertion — the same 34 tests in `test_definition_order.py` should still collect and pass.
- `__init__.py` public exports are unchanged — `git diff -- django_strawberry_framework/__init__.py` for this pass's working-tree delta is empty.
- No DRY scan is required — the apply-changes diff is two lines net (one removal + one replacement).
- No new helper, no new test, no new import. The `# noqa: F821` comments on the typo-lookalike test's `id: "NotNodeID[int]"` and `id: "MyNodeID[int]"` annotations stay unchanged.

### Notes for Worker 1 (spec reconciliation)

None expected. Worker 1 already edited the spec to rev 11 as part of the revision-plan pass (status line at `:4`, Decision 7 pseudocode at `:654-657`, and revision history block — see `### Spec changes made (Worker 1 only)` at line 552 of this artifact). This pass 2 lands the implementation exactly as the rev11 pseudocode specifies; no further spec edit is warranted.

---

## Review (Worker 3, pass 2)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None. The pass-2 revision is a 2-line net dead-code/dead-call removal; no DRY surface is in play.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns no output. `__all__` and the re-export list are unchanged. Matches the spec Definition of done's "no new public exports" requirement.

### CHANGELOG sanity

Not applicable; revision did not modify `CHANGELOG.md`.

### Documentation / release sanity

Worker 1 edited the active spec at `docs/spec-015-consumer_overrides_scalar-0_0_6.md` to revision 11 as part of the revision-plan pass (recorded under `### Spec changes made (Worker 1 only)` in this artifact at line 552). Re-verified against the on-disk spec:

- **Status line (`:4`)** — reads `Status: draft (revision 11, post-build maintainer-feedback pass).` Matches Worker 1's recorded change verbatim.
- **Decision 7 pseudocode (`:629-669`)** — the post-`except`-block success path is now the single-line `return _has_node_id_marker(hints.get("id"))` at `:669`, preceded by an inline rev11 comment block at `:655-668` documenting why the redundant guard was dropped (unreachable under call-site precondition; redundant given `_has_node_id_marker(None)` already short-circuits; blocked the 100% coverage gate). The rev8 M1 narrative comment block above the success path (`:650-654`) is preserved. The replacement removed the three-line `id_hint = hints.get("id"); if id_hint is None: return False; return _has_node_id_marker(id_hint)` block that rev8 M1 specified.
- **Revision 11 history entry (`:60-61`)** — appended a new revision-11 paragraph documenting the M1 dead-code fix and the L1 nit's test-file-local scope (with the explicit "no spec edit required for L1" rationale). The rev10 entry at `:55-59` is preserved unchanged. Chain intact.

No other docs/release/KANBAN/archive surfaces were touched by this pass (per `git diff` against the named files: `tests/types/test_definition_order.py` and `django_strawberry_framework/types/base.py` are the only two with pass-2-attributable hunks; the other M / MM entries in `git status --short` are carry-over from Slices 2-5 of the original build plus Worker 1's rev11 spec edit, all out of scope for this re-review).

### What looks solid

- **M1 implementation matches Worker 1's rev11 plan exactly.** The three-line block at the old `base.py:123-125` (`id_hint = hints.get("id"); if id_hint is None: return False; return _has_node_id_marker(id_hint)`) is replaced with the single-line `return _has_node_id_marker(hints.get("id"))` at `base.py:123`. `grep -n "id_hint is None\|id_hint = hints.get" django_strawberry_framework/types/base.py` returns 0 hits.
- **L1 edit lands at the right site.** `grep -n "registry.clear()" tests/types/test_definition_order.py | head -10` returns three remaining call sites: `:32` and `:34` inside the `_isolate_registry` autouse fixture (pre-existing fixture cleanup), and `:712` inside the unresolved-NodeID-shaped-string `finally` block (rev9 L1 + rev10 M2 mandated recipe; correctly retained because that test DOES register state — the H1 guard passes for the rev8 M2 accept case, so the synthetic `UnresolvedRelayChild` class enters the registry and must be cleared). The `registry.clear()` between the two `pytest.raises` blocks in `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` (the rev10 L1 site Worker 2 was instructed to drop) is gone — verified by reading lines 610-640 of the test file: the second `pytest.raises(ConfigurationError)` block at `:626` now directly follows the first block's `assert "GlobalID" in msg` at `:624` with one blank line, no `registry.clear()` between.
- **Helper structure after the edit.** `_id_annotation_is_relay_node_id` at `base.py:84-123` retains its docstring intact, retains the `try / except (NameError, AttributeError)` shape, retains the rev8 M2 fail-soft sub-case logic (string regex match + Annotated-object fallback), and the success path now delegates directly to `_has_node_id_marker(hints.get("id"))` as the rev11 pseudocode specifies. `_has_node_id_marker(None)` is verifiably safe under the lazy conjunction (`typing.get_origin(None) is Annotated` evaluates False, short-circuiting before `typing.get_args` runs).
- **No surprise edits.** `git diff -- django_strawberry_framework/types/base.py tests/types/test_definition_order.py` shows exactly the two atomic edits Worker 1's revision plan called for: a 4-to-1 line replacement in `types/base.py` after the `except` block, and a 2-line removal (one `registry.clear()` line plus one blank line) in `test_definition_order.py` between the typo-lookalike test's two `pytest.raises` blocks. No other deltas in these two files. Net: -2 lines in `base.py`, -2 lines in `test_definition_order.py`.
- **Focused tests pass.** `uv run pytest tests/types/test_definition_order.py tests/types/test_relay_interfaces.py --no-cov -q` → 96 passed in 2.84s (matches Worker 2's pass-2 report exactly).
- **Broader sweep clean.** Ran `uv run pytest --no-cov -q` → 707 passed, 2 skipped in 25.92s. No regression in pass count from the maintainer's externally-run baseline of 707 passed / 2 skipped (the maintainer's `docs/feedback.md` "Test run" note); the L1 edit removes a setup line, not an assertion, and the M1 edit removes unreachable code, so test counts are stable by construction.
- **Spec rev11 internally consistent.** Worker 1's three named spec edits (status line at `:4`, Decision 7 pseudocode at `:654-669`, revision-history entry at `:60-61`) all land on disk and match the artifact's `### Spec changes made (Worker 1 only)` description. The rev8 M1 comment block above the success path is preserved (audit trail intact); the new rev11 comment block at `:655-668` documents the rev8→rev11 transition explicitly.
- **Helper skip correctly recorded.** Worker 2 did not invoke `scripts/review_inspect.py` for this pass — pure dead-code removal does not add logic, so the BUILD.md "When to run the helper during build" thresholds (Worker 3 helper required when the slice adds 30+ lines of new logic) do not fire. Skip is the correct default for this revision; recorded here for completeness.

### Temp test verification

Not applicable; no temp tests for the revision.

### Notes for Worker 1 (spec reconciliation)

- **No further spec edits warranted.** Worker 1's rev11 edits (status line, Decision 7 pseudocode, revision history) match the on-disk spec verbatim and are internally consistent. The rev11 comment block at `:655-668` of the spec preserves the rev8-vs-rev11 audit trail as Worker 1 intended.
- **Build-plan checkbox is Worker 0's responsibility.** The artifact's revision plan correctly noted at `:573-575` that re-ticking the Slice 1 checkbox at `docs/builder/build-015-consumer_overrides_scalar-0_0_6.md:22` falls to Worker 0 after Worker 1's pass-2 `final-accepted` lands. The current checkbox state on disk is `- [ ]` (un-ticked) per Worker 0's revision dispatch; no Worker 3 action required.
- **Integration and Final gates remain un-ticked.** `docs/builder/build-015-consumer_overrides_scalar-0_0_6.md:27-28` shows `- [ ]` for both, matching the maintainer's framing that those downstream gates re-run after this Slice 1 revision loop closes.

### Review outcome

`review-accepted`

---

## Final verification (Worker 1, pass 2)

- **Maintainer feedback M1 — dead code removed**: pass. `grep "id_hint" django_strawberry_framework/types/base.py` returns 0 hits. The redundant `id_hint = hints.get("id"); if id_hint is None: return False; return _has_node_id_marker(id_hint)` block is gone; the success path now delegates directly to `return _has_node_id_marker(hints.get("id"))`. The dead line that the maintainer's coverage-aware test pass flagged at `base.py:125` no longer exists in source, so the 100% coverage gate is unblocked at the line level. The maintainer's CI run is the canonical confirmation that coverage restores to 100%; per BUILD.md "Coverage is the maintainer's gate, not a worker's tool", Worker 1 does not run `--cov*` here.
- **Maintainer feedback L1 — unnecessary `registry.clear()` removed**: pass. `grep -n "registry.clear()" tests/types/test_definition_order.py` returns three remaining sites: lines 32 + 34 inside the `_isolate_registry` autouse fixture (per-test cleanup) and line 712 inside the rev8 M2 unresolved-NodeID-shaped-string `finally` block (rev9 L1 mandated cleanup for a test where class creation actually succeeds and registers state). The `registry.clear()` previously between the two `pytest.raises(ConfigurationError)` blocks in `test_consumer_id_typo_lookalike_nodeid_string_on_relay_node_type_raises` (originally at `:626`) is gone — read of `tests/types/test_definition_order.py:610-640` confirms the second `pytest.raises(ConfigurationError) as exc_info:` at `:626` directly follows the first block's `assert "GlobalID" in msg` at `:624` with one blank line, no intervening `registry.clear()` call.
- **Spec rev 11 internal consistency**: pass. Worker 1's three named earlier spec edits are coherent on disk:
  - Status line at `docs/spec-015-consumer_overrides_scalar-0_0_6.md:4` reads `Status: draft (revision 11, post-build maintainer-feedback pass).` (verified).
  - Decision 7 pseudocode success path at `spec:669` is the single line `return _has_node_id_marker(hints.get("id"))`, preceded by the rev11 rationale comment block at `:655-668`. The rev8 M1 comment block at `:650-654` is preserved (audit trail intact).
  - Revision 11 history entry appended at `spec:60-61` (read end-to-end during artifact read; chain from rev1 through rev11 unbroken).
- **Existing tests still pass — broader scope**: pass. `uv run pytest --no-cov` → `707 passed, 2 skipped, 3 warnings in 25.38s`. Test count unchanged from the original final-gate baseline (707 passed / 2 skipped per `bld-final.md`). The L1 edit removed a setup line, not an assertion; the M1 edit removed unreachable code; counts are stable by construction. No `--cov*` flags used.
- **Coverage gate — maintainer-owned**: per BUILD.md "Coverage is the maintainer's gate, not a worker's tool", Worker 1 does not verify coverage at this gate. The M1 fix removes the single uncovered line the maintainer's external coverage-aware test pass identified (`base.py:125` in the pre-revision tree). The dead line is verifiably gone (zero `id_hint` grep hits); the maintainer is to re-run coverage at PR time to confirm 100% restoration.
- **Spec slice checklist tick state**: pass. No new sub-checks were added in pass 2 (no new tests, no new helpers, no new spec sub-bullets). The artifact's `### Spec slice checklist (verbatim)` ticks established in the pass-1 final verification remain valid; no change.
- **Final status**: `final-accepted`.

### Summary

Pass 2 closes the Slice 1 loop on the maintainer's post-close coverage-aware feedback. The M1 dead-code line at `base.py:125` is removed (Worker 2's pass-2 apply-changes edit delegated `_id_annotation_is_relay_node_id`'s success path directly to `_has_node_id_marker(hints.get("id"))`); the L1 unnecessary `registry.clear()` between the two `pytest.raises` blocks in the typo-lookalike test is dropped. The full suite at `uv run pytest --no-cov` reports `707 passed / 2 skipped` — same count as the original final-gate baseline, confirming the revision removed only dead code (M1) and an unnecessary setup line (L1) without altering any test contract. The spec rev 11 edits (status line, Decision 7 pseudocode tightening, Revision 11 history entry) are all on disk and internally consistent. The maintainer should re-run coverage at PR time to confirm the gate's `fail_under = 100` is restored; Worker 1 cannot verify coverage per BUILD.md.

### Spec changes made (Worker 1 only)

None in this pass; the spec edit was recorded in the Maintainer-feedback revision plan (Worker 1) section above.
