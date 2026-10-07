# Spec: `DjangoListField` (non-Relay list)

Target release: `0.0.7`.
Status: shipped (`0.0.7`, 2026-05-27); archived. Card `DONE-020-0.0.7`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [`DjangoType`][glossary-djangotype], [`Meta.fields`][glossary-metafields], [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook], [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`Relation handling`][glossary-relation-handling], [`Meta.primary`][glossary-metaprimary], [`Relay Node integration`][glossary-relay-node-integration], [`DjangoListField`][glossary-djangolistfield]), [`KANBAN.md`][kanban] card `DONE-020-0.0.7`, predecessor spec [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (Decision 9 - async `get_queryset` shape) and [`docs/SPECS/spec-018-meta_primary-0_0_6.md`][spec-018] (multiple `DjangoType`s per model).

The reasons behind each Decision and the alternatives it rejected live in [`spec-020-list_field-0_0_7-rationale.md`][spec-020-rationale]. This file states the contract. The field's `offset` / `limit` / `orderBy` argument surface is owned by [`spec-050-list_field_arguments-0_0_15.md`][spec-050]; this spec owns the field, its resolver, its validation, and its row bound.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoListField`][glossary-djangolistfield] — `shipped (0.0.7)`; the entry this spec owns.
- [`DjangoType`][glossary-djangotype] — the type class the field binds to; the field's queryset is derived from `Meta.model` (see [Decision 2](#decision-2--default-resolver-shape)).
- [`Meta.model`][glossary-metamodel] — the source of `model._default_manager` (see [Decision 2](#decision-2--default-resolver-shape)).
- [`Meta.fields`][glossary-metafields] — independent of this field; `DjangoListField` does not introspect a type's selected fields.
- [`get_queryset` visibility hook][glossary-get-queryset-visibility-hook] — applied to the default queryset before return (see [Decision 3](#decision-3--get_queryset-and-async-symmetry)).
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — root-gated planning; the field returns a `QuerySet` so the `info.path.prev is None` gate fires (see [Decision 4](#decision-4--optimizer-cooperation)).
- [`Relation handling`][glossary-relation-handling] — many-side relations produce `list[T]` via generated resolvers; `DjangoListField` is the symmetric **root**-list primitive and does NOT change relation-side many-list shapes (see [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields)).
- [`Meta.primary`][glossary-metaprimary] — multiple `DjangoType`s per model; `DjangoListField(SecondaryType)` is the explicit-target shape that side-steps the registry lookup ambiguity (see [Decision 6](#decision-6--metaprimary-interaction)).
- [`Relay Node integration`][glossary-relay-node-integration] — non-Relay list shape is the entire point of this field; the Relay sibling lives under [`DjangoConnectionField`][glossary-djangoconnectionfield] in `DONE-030-0.0.9` (see [Decision 8](#decision-8--out-of-scope-boundary-with-djangoconnectionfield)).
- [`ConfigurationError`][glossary-configurationerror] — raised by the field's constructor when the argument is not a registered `DjangoType` subclass (see [Decision 5](#decision-5--validation--error-shapes)).

Project conventions to follow:

- [`AGENTS.md`][agents] — test placement: a line a real fakeshop query reaches is pinned at the live `/graphql/` tier in `examples/fakeshop/test_query/`.
- [`CONTRIBUTING.md`][contributing] — 100% coverage gate; the single-sourced version.
- [`KANBAN.md`][kanban] — the `DONE-020-0.0.7` card.
- [`docs/TREE.md`][tree] — package and test layout; a flat single-file module at the package root pairs with `tests/test_<module>.py`.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 0: Strawberry facts the design rests on (no repo code)
  - [ ] `from strawberry.types import Info` is the `info` annotation; Strawberry raises `MissingArgumentsAnnotationsError` for an unannotated resolver parameter, so a bare `lambda root, info: ...` cannot be the field's resolver.
  - [ ] A `strawberry.field(resolver=...)` value assigned to an annotated class attribute under `@strawberry.type` takes its GraphQL type from the attribute annotation: `list[BranchType]` renders `[BranchType!]!`, `list[BranchType] | None` renders `[BranchType!]`. Introspection (`kind` / `ofType` chain), not SDL text, is how the tests read the rendered type.
- [ ] Slice 1: Module + factory function
  - [ ] Flat module `django_strawberry_framework/list_field.py` (placement decision: see [Decision 1](#decision-1--module-location-mechanism--public-export)) houses the `DjangoListField` symbol.
  - [ ] `DjangoListField` is a **factory function**. The factory returns `strawberry.field(resolver=<wrapped>, description=..., deprecation_reason=..., directives=...)`. Consumer usage is `all_branches: list[BranchType] = DjangoListField(BranchType)` — Strawberry reads the consumer's class-attribute annotation for the outer GraphQL list shape (`list[BranchType]` → `[BranchType!]!`, `list[BranchType] | None` → `[BranchType!]`), so the factory does NOT need to override the annotation.
  - [ ] `ruff` rule **N802** is suppressed on the `def DjangoListField(...)` line with a per-line `# noqa: N802` naming graphene-django parity: the PascalCase shape is intentional, and a per-file ignore would hide future violations.
  - [ ] `target_type` is captured via closure; it is never a first positional resolver argument. The wrapper's published signature is synthesized by `_synthesized_list_signature` as `(root, info: strawberry.types.Info)` plus the list arguments [`spec-050`][spec-050] owns, because Strawberry treats every signature parameter as a GraphQL argument.
  - [ ] Default resolver body: `base_queryset(target_model)` (`django_strawberry_framework/utils/querysets.py::base_queryset`, the `model._default_manager.all()` seed), then `django_strawberry_framework/list_field.py::_execute_queryset_pipeline_sync` or `::_execute_queryset_pipeline_async` — the visibility hook first (`apply_type_visibility_sync` / `apply_type_visibility_async`; an async `get_queryset` met on the sync path is rejected with `SyncMisuseError` per [Decision 3](#decision-3--get_queryset-and-async-symmetry)), then any ordering and offset guard, then the row bound LAST through `django_strawberry_framework/resource_policy.py::_windowed_rows`, after the visibility hook has composed onto the unsliced source.
  - [ ] Async detection uses the same `django_strawberry_framework/utils/execution_mode.py::async_execution` predicate the Relay defaults use (`django_strawberry_framework/types/relay.py #"from ..utils.execution_mode import async_execution"`).
  - [ ] Optional `resolver=` constructor argument that overrides the default body. The consumer resolver is wrapped so a `Manager`/`QuerySet` return value is fed through `target_type.get_queryset(qs, info)` (graphene-django parity). The wrapper itself does the `Manager → QuerySet` coercion (`django_strawberry_framework/utils/querysets.py::prepared_resolver_source`) BEFORE applying `get_queryset` (the optimizer's downstream normalization is a safety net, not a substitute). **Two arms, chosen at construction time**: an async callable (`django_strawberry_framework/utils/typing.py::is_async_callable` — the wrapper-aware superset of `inspect.iscoroutinefunction`, which also sees an `async def __call__` instance, a `functools.partial`, and a raw `staticmethod` descriptor), or any other callable, an async generator function included. The async-callable arm builds an `async def` wrapper that `await`s the consumer's coroutine BEFORE the isinstance check, so an async resolver returning a `QuerySet` still gets `get_queryset` applied. The sync arm additionally detects an async-only iterable return at call time and rejects it with `SyncMisuseError` when execution is synchronous. Python `list` returns from either arm pass through unchanged apart from the row window (offset, limit, row bound). There is no runtime-coroutine fallback and none is needed: a sync resolver that returns a coroutine, a custom awaitable, or a `Future` is rejected loudly (see [Edge cases and constraints](#edge-cases-and-constraints)). Optimizer cooperation still applies because the extension is root-gated against `info.path.prev is None` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`); a consumer resolver returning a `QuerySet` is planned exactly like the default.
  - [ ] Optional `description=` / `deprecation_reason=` / `directives=` pass-through into the inner `strawberry.field(...)` call so the symbol is feature-comparable to `strawberry.field(...)` at the metadata level, plus the `max_rows=` / `trusted_max_rows=` row-bound arguments validated per [Decision 5](#decision-5--validation--error-shapes).
  - [ ] `django_strawberry_framework/__init__.py` re-exports `DjangoListField` and lists it in `__all__` ([Decision 1](#decision-1--module-location-mechanism--public-export)); `tests/base/test_init.py` pins `__all__`.
- [ ] Slice 2: Validation
  - [ ] Constructor validates that the argument is a class AND is `issubclass(arg, DjangoType)` AND carries its **own** registered definition (`definition.origin is arg` and the definition is the registry's exact object, never `hasattr`) — per [Decision 5](#decision-5--validation--error-shapes). Errors raise `ConfigurationError` with messages that open with the factory name (`DjangoListField ...`).
  - [ ] `resolver=`, when supplied, is callable; otherwise `ConfigurationError`.
  - [ ] `max_rows=` is a positive integer and `trusted_max_rows=` is exactly a `bool`, checked before the target; `directives=` is a sequence of directive instances, checked after it.
  - [ ] The validation tests live in `tests/test_list_field.py` (construction-time errors never reach a schema).
- [ ] Slice 3: Optimizer + `get_queryset` cooperation tests
  - [ ] Behavior tests, all at the live tier (`examples/fakeshop/test_query/test_list_field_api.py`, `test_list_field_async_api.py`, `test_library_api.py`) because a real query reaches each: default-resolver `cls.get_queryset` invocation, sync rejection of an async `get_queryset`, async path awaits `get_queryset`, **sync and async consumer `resolver=` returns receive `get_queryset` when they are a `Manager`/`QuerySet`**, Python-`list` consumer returns pass through unchanged, nullable-outer-via-consumer-annotation produces `[T!]`, non-nullable-outer default produces `[T!]!`, `DjangoListField` at root position is optimized, [FK-id elision][glossary-fk-id-elision] survives, `Meta.primary` interaction (explicit primary, explicit secondary). See [Test plan](#test-plan) for the names.
- [ ] Slice 4: Live HTTP coverage
  - [ ] Root fields in `examples/fakeshop/apps/library/schema.py` — `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` for the default-resolver path, `all_library_branches_via_list_field_nullable: list[BranchType] | None` for the nullable-outer rendering, and `all_library_branches_via_list_field_manager_resolver` for a consumer resolver returning a `Manager`, beside the hand-written `all_library_branches` (whose `order_by("id")` `test_library_relation_override_shapes_http_response_data` depends on).
  - [ ] HTTP tests in `examples/fakeshop/test_query/test_library_api.py` asserting: (a) the field returns the expected branches via `/graphql/`, (b) the optimizer planned `prefetch_related` / `select_related` for a nested selection (exact query count), (c) the default resolver applies `get_queryset` (`test_branches_via_list_field_default_resolver_applies_get_queryset_live`: the shipped `BranchType.get_queryset` hides `city="restricted"` branches from the anonymous client).
- [ ] Slice 5: Docs and board
  - [ ] [`DjangoListField`][glossary-djangolistfield] reads `shipped (0.0.7)` in [`docs/GLOSSARY.md`][glossary] (rendered from the fakeshop glossary database), in the public exports list and the index table.
  - [ ] [`README.md`][readme], [`docs/README.md`][docs-readme], [`GOAL.md`][goal] and [`TODAY.md`][today] name `DjangoListField` as shipped, never as a "wait for" item.
  - [ ] `docs/TREE.md` (rendered from module docstrings) lists `list_field.py` and `tests/test_list_field.py`; `DjangoListField` has one home, `list_field.py`.
  - [ ] `KANBAN.md` carries the shipped `DONE-020-0.0.7` card (rendered from the fakeshop kanban database), in add-only language: the field was added beside the hand-written `all_library_*` resolvers, replacing none.
  - [ ] `CHANGELOG.md` `[0.0.7]` Added entry: `DjangoListField` (non-Relay `list[T]` field for **root Query fields** with default `model._default_manager.all()` resolver, `cls.get_queryset` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns, optimizer cooperation through root-gating).
  - [ ] The version bump follows [Decision 10](#decision-10--joint-007-cut).
  - [ ] One public export (`DjangoListField`) belongs to this spec.

## Problem statement

Without a list primitive, every model-backed root `list[T]` field of a `DjangoType` is a hand-rolled resolver of one mechanical shape:

```python
@strawberry.field(graphql_type=list[BranchType])
def all_library_branches(self) -> QuerySet[models.Branch]:
    return models.Branch.objects.order_by("id")
```

Consequences without a `DjangoListField`:

- Every Django app that wants a model collection through GraphQL writes a one-line root resolver per model, identical except for the model and target type.
- `graphene-django` migrants lose a primitive they already know (`graphene_django/fields.py::DjangoListField` — `class DjangoListField(Field)` is the default list shape for graphene-django).
- The `cls.get_queryset(...)` visibility hook is silently bypassed unless the consumer remembers to thread it through every hand-rolled resolver.
- Nothing distinguishes the simple-list case from the Relay-connection case.

The seams the field needs are all in place: `DjangoTypeDefinition.model` for the queryset source, `cls.get_queryset(...)` for the visibility hook, `DjangoOptimizerExtension`'s root-gated planning hook (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve #"if info.path.prev is not None:"`), and the sync + async visibility helpers `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` / `::apply_type_visibility_async` (the sync one rejects an async hook with `SyncMisuseError`, a `ConfigurationError` subclass). `DjangoListField` takes an explicit `DjangoType` argument, NOT a model, so the registry's primary/secondary ambiguity is irrelevant to the construction path.

The target is not a full connection/query-field release. The target is to make `list[T]` **root** fields possible in the package's `class Meta` style, while preserving the optimizer behavior, the `get_queryset` cooperation contract, and the `Meta.primary` registry semantics. Nested non-root usage of `DjangoListField` is functional (the field still produces a list resolver) but is NOT root-optimized per [Decision 4](#decision-4--optimizer-cooperation).

## Goals

1. Ship `DjangoListField(TargetType)` as a public export from `django_strawberry_framework` — a factory function that returns `strawberry.field(resolver=..., ...)`. The default resolver calls `model._default_manager.all()` and applies `cls.get_queryset(...)`; sync + async paths; consumer-`resolver=` override is supported, and the override's `Manager`/`QuerySet` return value also receives `target_type.get_queryset(...)` (graphene-django parity).
2. Preserve `DjangoOptimizerExtension`'s root-gated planning for `DjangoListField`-served querysets at **root** Query positions. Nested non-root use of `DjangoListField` works as a resolver but is NOT root-optimized; see [Decision 4](#decision-4--optimizer-cooperation).
3. Preserve the `cls.get_queryset(...)` cooperation contract from [`spec-015-relay_interfaces-0_0_5.md`][spec-015] and [`docs/GLOSSARY.md#get_queryset-visibility-hook`][glossary-get-queryset-visibility-hook]: both the sync and the async paths invoke `cls.get_queryset(qs, info)` before returning, and an async `get_queryset` met on the sync path is rejected with `SyncMisuseError` — the [`ConfigurationError`][glossary-configurationerror] subclass raised by `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` (via `django_strawberry_framework/utils/querysets.py::reject_async_in_sync_context`), the same rejection every read surface receives.
4. Stay tight: no `DjangoConnectionField`, no filter / aggregate / search arguments on the field (its `offset` / `limit` / `orderBy` surface is [`spec-050`][spec-050]'s), no auto-upgrade of reverse-FK / M2M relation fields, no node-aware optimizer feature work beyond preserving root-gated planning.
5. An `all_library_branches_via_list_field` root field in the `library` example, beside the hand-written `all_library_branches` (whose `order_by("id")` HTTP tests depend on), gives the default `DjangoListField` resolver a live HTTP-tested home.

## Non-goals

- `DjangoConnectionField` and the Relay-shaped pagination surface. Tracked under `DONE-030-0.0.9` in [`KANBAN.md`][kanban].
- Filter / search / aggregate input arguments on `DjangoListField`. Those are the Layer-3 read-side primitives tracked in `DONE-027-0.0.8` (filters), `TODO-BETA-047-0.1.2` (search), `TODO-BETA-049-0.1.3` (aggregates); the `orderBy` argument (over `DONE-028-0.0.8`'s ordersets) and `offset` / `limit` are [`spec-050`][spec-050]'s.
- Cascade permissions and field-level permissions. Tracked under `DONE-034-0.0.10`. `DjangoListField` needs no cascade-specific code: [`apply_cascade_permissions`][glossary-apply-cascade-permissions] is called from a type's own `cls.get_queryset(...)`, and the field applies that hook, so a cascading target narrows the list with no participation from this field (`examples/fakeshop/test_query/test_list_field_api.py::test_holder_item_list_field_drops_rows_under_a_hidden_category`).
- Auto-upgrading reverse-FK / M2M many-side relation fields to `DjangoListField`. Relation many-side fields are already shipped as `list[T]` via generated resolvers (see [`Relation handling`][glossary-relation-handling]); `DjangoListField` is the **root** primitive, not a relation-side replacement. See [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields).
- [Multi-database][glossary-multi-database-cooperation] / sharding-aware queryset routing. Tracked under `DONE-023-0.0.7` (the multi-db cooperation contract). `DjangoListField` uses `model._default_manager.all()` which Django routes through the configured database router automatically; nothing in this card precludes the cooperation contract that lands alongside.
- Cursor pagination and ordering defaults. `DjangoListField` adds no order tiebreaker and no cursors; the Relay-connection field is the home for both. The `offset` / `limit` window is [`spec-050`][spec-050]'s. Row **limits** are neither out of scope nor optional: every `DjangoListField` is row-bounded, see [Row bound](#row-bound).
- A flat-list helper class shape that wraps every `DjangoType` declaration (e.g., `class MyTypeListField(DjangoListField): pass`). Not needed; `DjangoListField(MyType)` at the call site is sufficient.

## Borrowing posture

The two reference packages at the paths given in `docs/TREE.md` ship a similar primitive. The slice should borrow patterns, not implementations.

### From `graphene-django` — borrow the user-facing shape

Source: `graphene_django/fields.py::DjangoListField` in the `graphene_django` checkout AGENTS.md names.

- **`DjangoListField` symbol name.** Same name, same role.
- **Default-resolver shape — model-derived manager → type-level visibility hook.** `graphene_django/fields.py::DjangoListField` (the `get_manager` / `list_resolver` methods) derives the manager from `_type._meta.model._default_manager`, calls `_type.get_queryset(queryset, info)`, returns the queryset. We borrow this contract verbatim. One adaptation: our `DjangoType.get_queryset` is a `classmethod`, not a `staticmethod` ([`docs/GLOSSARY.md#get_queryset-visibility-hook`][glossary-get-queryset-visibility-hook]).
- **Item-level non-null; outer-level via consumer annotation.** `graphene_django/fields.py::DjangoListField.__init__ #"List(NonNull(_type))"` wraps the type as `List(NonNull(_type))`. We borrow the item-non-null part (Django ORM never returns `None` rows from a queryset); the outer nullability is driven by the **consumer's class-attribute annotation** rather than a constructor kwarg (`list[BranchType]` → `[BranchType!]!`, `list[BranchType] | None` → `[BranchType!]`).
- **`maybe_queryset` coercion of `Manager`-shaped returns + `get_queryset` application on consumer-resolver returns.** `graphene_django/fields.py::DjangoListField.list_resolver` calls `maybe_queryset(...)` so a consumer resolver returning `Model.objects` (the Django shorthand) is coerced via `.all()`, AND then applies `_type.get_queryset(queryset, info)` to any `QuerySet` returned. We borrow BOTH halves of this — the **field wrapper itself** performs the `Manager → QuerySet` coercion (`django_strawberry_framework/utils/querysets.py::prepared_resolver_source`) BEFORE applying `target_type.get_queryset(...)` so the visibility hook receives a `QuerySet`, not a `Manager`. `DjangoOptimizerExtension._optimize`'s own normalization through `django_strawberry_framework/utils/querysets.py::normalize_query_source` is a downstream safety net for non-`DjangoListField` root resolvers that happen to return `Model.objects`; the two coercions co-exist (one for visibility-hook correctness inside the field, one for optimizer cooperation at the extension boundary). The `get_queryset` application on consumer-resolver returns is explicit in the field wrapper, and applies whether the consumer supplied a sync or an `async def` resolver. Consumers who genuinely want to bypass `get_queryset` return a Python `list` (already-evaluated) from their resolver; the field detects this and passes the list through unchanged.

### Explicitly do not borrow

- Graphene-django's `wrap_resolve` machinery (`graphene_django/fields.py::DjangoListField.wrap_resolve`). Strawberry's resolver assignment is direct (`strawberry.field(resolver=...)`), and graphene-django's `partial(self.list_resolver, …)` wrapping is the graphene-side equivalent. We use Strawberry's native shape.
- Graphene-django's `_type.of_type.of_type` unwrap dance (`graphene_django/fields.py::DjangoListField.wrap_resolve #"_type.of_type.of_type"`) — the type wrapping is different in Strawberry; we annotate `list[T]` directly.
- `strawberry-graphql-django` does NOT ship a direct `DjangoListField` analogue — its closest primitive is `strawberry_django.field()` returning a `list[T]` of a strawberry-django type. That mechanism is decorator-based and contradicts the `class Meta`-driven posture in [`README.md`][readme] and [`GOAL.md`][goal]. No borrow there.

## User-facing API

The consumer surface is one public export, `DjangoListField`, from `django_strawberry_framework`.

### Default usage — root list field

```python path=null start=null
import strawberry
from django_strawberry_framework import (
    DjangoListField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
)
from apps.library import models


class BranchType(DjangoType):
    class Meta:
        model = models.Branch
        fields = ("id", "name", "city", "shelves")


@strawberry.type
class Query:
    all_library_branches: list[BranchType] = DjangoListField(BranchType)


finalize_django_types()

schema = strawberry.Schema(
    query=Query,
    extensions=[DjangoOptimizerExtension()],
)
```

Expected GraphQL behavior:

- `Query.allLibraryBranches: [BranchType!]!` (item-non-null + list-non-null by default).
- The resolver returns `Branch._default_manager.all()`, threaded through `BranchType.get_queryset(qs, info)` and then row-bounded (see [Row bound](#row-bound)).
- **No order guarantee.** The default resolver appends no tiebreaker, so response order is database-dependent unless the model declares `Meta.ordering` or the query passes `orderBy` (see [Decision 8](#decision-8--out-of-scope-boundary-with-djangoconnectionfield)).
- `DjangoOptimizerExtension` plans `select_related` / `prefetch_related` / [`only()`][glossary-only-projection] for nested selections.
- Async resolvers awaiting `BranchType.get_queryset` work without consumer wiring.

### Custom resolver override

```python path=null start=null
from typing import Any

from strawberry.types import Info


def _branches_with_recent_loans(root: Any, info: Info) -> models.QuerySet:
    return models.Branch.objects.filter(shelves__books__loans__isnull=False).distinct()


@strawberry.type
class Query:
    branches_with_recent_loans: list[BranchType] = DjangoListField(
        BranchType,
        resolver=_branches_with_recent_loans,
    )
```

When `resolver=` is supplied, the consumer's body runs instead of the default `model._default_manager.all()` call. The field then applies `BranchType.get_queryset(qs, info)` to the return value when it is a `Manager` or `QuerySet` (graphene-django parity per `graphene_django/fields.py::DjangoListField.list_resolver`). Consumers who genuinely want to bypass `get_queryset` return a Python `list` (already-evaluated) from their resolver — a non-queryset iterable passes through unchanged.

**Async consumer resolvers**: an async resolver returning a `Manager`/`QuerySet` is awaited before the `isinstance` check, so `get_queryset` is applied to the awaited value — async-vs-sync is not a contract surface. The factory decides the wrapper shape at construction time with `django_strawberry_framework/utils/typing.py::is_async_callable`, which sees an `async def`, an instance whose `__call__` is `async def`, a raw `staticmethod` descriptor, and any nesting of `functools.partial` / `staticmethod` layers around those. That predicate is the authority for which spellings count; the field factory does not keep its own list. An **async generator** resolver, and a sync resolver returning an async-only iterable, are both supported too and are both bounded; an async-only iterable met from synchronous execution raises `SyncMisuseError` rather than yielding nothing (see [Decision 2](#decision-2--default-resolver-shape)).

```python path=null start=null
# Async-resolver example. Django's ORM is sync-by-default, so the typical
# shape wraps the queryset construction in ``sync_to_async``. The returned QuerySet
# still receives ``BranchType.get_queryset(...)`` exactly like the sync example above.
from asgiref.sync import sync_to_async


async def _branches_with_recent_loans_async(root: Any, info: Info) -> models.QuerySet:
    return await sync_to_async(
        lambda: models.Branch.objects.filter(
            shelves__books__loans__isnull=False,
        ).distinct()
    )()


@strawberry.type
class Query:
    branches_with_recent_loans_async: list[BranchType] = DjangoListField(
        BranchType,
        resolver=_branches_with_recent_loans_async,
    )
```

Resolver signature is the Strawberry-native `(root: Any, info: Info)` shape (`info` MUST be annotated `strawberry.types.Info` or Strawberry's schema construction raises `MissingArgumentsAnnotationsError`; `**kwargs` is NOT a harmless catch-all because Strawberry treats every parameter as a GraphQL argument). The field's own `offset` / `limit` / `orderBy` arguments are [`spec-050`][spec-050]'s.

Optimizer cooperation still applies because the optimizer extension is root-gated and runs on whatever queryset the field returns.

### Nullable outer list

The outer-list nullability is controlled by the **consumer's class-attribute annotation** (`DjangoListField` does NOT take a `nullable_list=` constructor argument). Strawberry reads the annotation directly to render the GraphQL type:

```python path=null start=null
all_branches: list[BranchType] = DjangoListField(BranchType)                  # [BranchType!]!  (non-null outer)
all_branches_or_none: list[BranchType] | None = DjangoListField(BranchType)   # [BranchType!]   (nullable outer)
```

Item-level non-null is the same in both shapes — Django ORM never returns `None` rows from a queryset.

### Row bound

Every `DjangoListField` is row-bounded, and the field's surface for that bound is two constructor arguments: `max_rows=` narrows the bound for this field, and `trusted_max_rows=True` is the only spelling that lets the field be wider than the request's policy. There is no unbounded spelling — `max_rows=None` means the policy governs. How the bound and the policy compose — that `max_list_rows` applies whether or not the field says anything, and which of the two wins — is the standing statement in [`docs/GLOSSARY.md#djangolistfield`][glossary-djangolistfield], the consumer-facing authority; the constructor guard that enforces the argument itself is [Decision 5](#decision-5--validation--error-shapes).

```python path=null start=null
all_library_branches: list[BranchType] = DjangoListField(
    BranchType,
    max_rows=50,            # narrows to the tighter of 50 and the request policy
    trusted_max_rows=False, # the default; True is the explicit widening opt-in
)
```

### Field-level GraphQL metadata

```python path=null start=null
all_library_branches: list[BranchType] = DjangoListField(
    BranchType,
    description="Every branch in the library system, ordered by Django default.",
    deprecation_reason=None,
    directives=(),
)
```

These pass through to the underlying Strawberry field unchanged.

## Architectural decisions

### Decision 1 — Module location, mechanism, & public export

**Mechanism.** `DjangoListField` is a **factory function**, not a class. It returns a `strawberry.field(resolver=<wrapped>, description=..., deprecation_reason=..., directives=...)` with the resolver wrapped per [Decision 2](#decision-2--default-resolver-shape). The consumer's class-attribute annotation (`all_branches: list[BranchType]`) is what Strawberry reads to derive the field's GraphQL type; the factory does not own or override that annotation.

**Module location.** `DjangoListField` lives in **`django_strawberry_framework/list_field.py`** (a flat single-file module at the package root), not in `connection.py`, which holds the Relay sibling.

**`list_field.py` is the home of the shared field-target validation contract.** The four constructor guards live here as `django_strawberry_framework/list_field.py::_validate_djangotype_target`, and the Relay-Node-shaped superset as `::_validate_relay_djangotype_target`. `DjangoConnectionField` (`django_strawberry_framework/connection.py #"from .list_field import _validate_relay_djangotype_target"`) and the root node fields (`django_strawberry_framework/relay.py::_validate_node_target`) both import the Relay variant, so the target-validation contract is single-sited in this module rather than duplicated per factory. Each caller passes its own `field=` name, so every `ConfigurationError` names the factory that raised it. A reader changing a guard changes it here, once.

Public-export surface:

- `django_strawberry_framework/__init__.py` imports `from .list_field import DjangoListField, ListArgumentError`.
- `__all__` lists `"DjangoListField"` in alphabetical position.
- `tests/base/test_init.py`'s pinned `__all__` assertion covers it.

The rejected placement alternatives (inlining into `__init__.py`, a `fields/` subpackage, relocating the target guards to `utils/`), the reasons `list_field.py` won over bundling into `connection.py`, and the mechanisms the installed Strawberry rules out are in [the rationale companion][spec-020-rationale].

### Decision 2 — Default resolver shape

The factory function captures `target_type` via closure and builds a wrapped resolver whose published signature matches Strawberry's contract: `_synthesized_list_signature` sets the wrapper's `__signature__` / `__annotations__` to `(root, info: strawberry.types.Info)` plus the published list arguments, because Strawberry treats every signature parameter as a GraphQL argument. Sketch of the shape (the module is authoritative):

```python path=null start=null
# django_strawberry_framework/list_field.py
def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity.
    target_type, *, resolver=None, description=None, deprecation_reason=None,
    directives=(), max_rows=None, trusted_max_rows=False,
):
    # max_rows / trusted_max_rows validation and the shared target guards (Decision 5).
    if resolver is None:
        def _default(*args, offset=None, limit=None, order_by=strawberry.UNSET, **kwargs):
            _, info, args_record = _argument_record(args, kwargs, ...)
            qs = base_queryset(target_model)
            if async_execution():
                return _execute_queryset_pipeline_async(node_type, qs, info, args_record, ...)
            return _execute_queryset_pipeline_sync(node_type, qs, info, args_record, ...)
        wrapped = _default
    else:
        # _async_wrap: await the consumer coroutine FIRST, then
        #   prepared_resolver_source(source, node_type, async_guard=reject_residual_async_source).
        # _sync_wrap: call the consumer; an async-only iterable goes through
        #   reject_async_iterable_in_sync_context(...) and is awaited by the executor;
        #   anything else goes through
        #   prepared_resolver_source(source, node_type, async_guard=reject_awaitable_sync_source).
        # A QuerySet source runs the queryset pipeline; any other iterable is windowed
        # by resource_policy.py::_windowed_rows and passes through otherwise unchanged.
        wrapped = _async_wrap() if is_async_callable(user_resolver) else _sync_wrap()
    signature, annotations = _synthesized_list_signature(orderset_class)
    wrapped.__signature__ = signature
    wrapped.__annotations__ = annotations
    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
```

The queryset pipeline (`django_strawberry_framework/list_field.py::_execute_queryset_pipeline_sync` / `::_execute_queryset_pipeline_async`) applies the visibility hook first (`apply_type_visibility_sync` / `apply_type_visibility_async` from `django_strawberry_framework/utils/querysets.py`, see [Decision 3](#decision-3--get_queryset-and-async-symmetry)), then any supplied ordering and offset guard, then the row bound through `_windowed_rows`. `prepared_resolver_source` is `django_strawberry_framework/utils/querysets.py::prepared_resolver_source`: it refuses the wrong async shape first, coerces a `Manager` to a `QuerySet`, and reports which branch the value landed in.

**Two consumer-resolver arms, plus a call-time check.** A consumer `resolver=` is either an async callable — `async def`, an instance whose `__call__` is `async def`, a raw `staticmethod` descriptor, or any nesting of `functools.partial` / `staticmethod` around those, as `django_strawberry_framework/utils/typing.py::is_async_callable` defines it (`django_strawberry_framework/utils/typing.py::_callable_inspection_target` peels both wrapper kinds in a loop, so the nesting depth is not a contract surface) — or any other callable, an async generator function included (calling it returns an async-only iterable rather than a coroutine). The arm is committed to at construction time; the sync arm additionally detects an async-only iterable at call time, because a sync callable may return one. An async-only iterable met from synchronous GraphQL execution is rejected with `SyncMisuseError` rather than silently yielding nothing: `django_strawberry_framework/utils/querysets.py::reject_async_iterable_in_sync_context` raises unless the operation's executor is async. `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_http_partial_async_generator_resolver_is_bounded`, `::test_async_generator_natural_exhaustion_does_not_call_aclose` and `examples/fakeshop/test_query/test_list_field_api.py::test_holder_sync_http_rejects_an_async_generator_resolver` pin the async-iterable path.

**The row bound is applied last, never before the visibility hook.** A sliced queryset cannot be refiltered or reordered, and both the visibility hook and the consumer post-processing compose onto the source — so slicing first would turn the bound into a crash on every type that declares a hook. The ordering is a correctness constraint, not a preference, which is why the async pipeline applies the bound to the awaited, visibility-composed queryset.

**Async-detection asymmetry — intentional, not a harmonization candidate**. Two different detection mechanisms appear above:

- The **default** resolver uses **runtime** `async_execution()` inside a plain `def _default(...)` body that lazily returns either a value or a coroutine. Strawberry handles `AwaitableOrValue` from sync resolvers, so the same factory output dispatches correctly under both `schema.execute_sync(...)` and `await schema.execute(...)`. This is the same pattern the optimizer extension uses at `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`.
- The **consumer-resolver wrapper** uses **construction-time** `is_async_callable(user_resolver)` to commit to either an `async def _wrap` or a plain `def _wrap`. The wrapper has to be statically sync OR async at factory time because Strawberry inspects the resolver's signature once at schema construction and commits to async-vs-sync handling globally — an `async def` wrapper lets Strawberry await it directly without going through `AwaitableOrValue`. The predicate is deliberately **not** `inspect.iscoroutinefunction`, which returns `False` for a `functools.partial` around an `async def`, for a callable object with an `async def __call__`, and for a raw `staticmethod` descriptor wrapping an `async def`.

Harmonizing the two would either force the default into static commitment (loses sync-callability) or force the consumer wrapper into lazy upgrade (adds an extra coroutine layer per call). Both mechanisms are correct for their respective dispatch sites; a future maintainer noticing the asymmetry should leave it alone.

Item-level non-null is unconditional — Django ORM never returns `None` rows from a queryset (matches `graphene_django/fields.py::DjangoListField.__init__ #"Django would never return a Set of None"`'s comment).

Outer-level nullability is driven by the **consumer's class-attribute annotation**: `list[T]` → `[T!]!`; `list[T] | None` → `[T!]`. The factory does NOT take a `nullable_list=` constructor argument because Strawberry already reads the class-attribute annotation; a separate kwarg would either fight or silently override it.

The rejected alternatives - a Python-`list` default return, skipping `cls.get_queryset` on consumer-resolver returns, a `nullable_list=` constructor argument, a first-positional `(type_cls, info)` signature, a catch-all `**kwargs`, `null=True` item types, and a runtime `inspect.iscoroutine(result)` fallback in the sync wrapper - are in [the rationale companion][spec-020-rationale], each with the reason it lost.

### Decision 3 — `get_queryset` and async symmetry

The sync + async `cls.get_queryset(...)` cooperation is delegated to the shared sealed-boundary helpers in `django_strawberry_framework/utils/querysets.py`, the single site every recomposing read surface uses — e.g. the Relay node defaults, the connection root, this field, and the cascade:

- `apply_type_visibility_sync(cls, qs, info)` at `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` — applies the hook in a sync context; rejects an async hook with `SyncMisuseError`, a `ConfigurationError` subclass that also inherits `RuntimeError`, after closing the unawaited coroutine (or cancelling a `Future`) so no "coroutine was never awaited" warning escapes. A caller may pass its own recourse wording; the list field passes none, so its rejection carries the helper's default (Relay node-defaults) recourse text.
- `apply_type_visibility_async(cls, qs, info)` at `django_strawberry_framework/utils/querysets.py::apply_type_visibility_async` — applies the hook in an async context; awaits awaitables; passes sync returns through.

Async detection re-uses the `django_strawberry_framework/utils/execution_mode.py::async_execution` predicate the Relay defaults use (`django_strawberry_framework/types/relay.py #"from ..utils.execution_mode import async_execution"`). The `list_field.py` module imports it from the same site; no fork.

**The hook's return crosses a sealed boundary.** The contract is not "call the hook and use what comes back". Both helpers SEAL the source and the hook's result into a fresh framework-owned plain `QuerySet` rebuilt from validated query state — shape, concrete and actual-base table, sealability, model-row-ness, routed alias — and fail closed on any return they cannot prove: a `Manager` whose `.all()` degrades to a non-queryset, a silently re-routed database, a `.values()` projection on a read surface, an instance-shadowed `all`, or a sliced result a later recomposition would have to reorder. A hostile or careless `get_queryset` override therefore cannot widen the rows this field serves, and an unprovable return raises rather than passing through. Pinned by `examples/fakeshop/test_query/test_list_field_api.py::test_shipped_branches_hostile_queryset_subclass_cannot_leak_restricted_rows` (and its async twin `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_hostile_queryset_subclass_cannot_leak_restricted_rows`), `examples/fakeshop/test_query/test_list_field_api.py::test_holder_manager_that_degrades_to_a_list_is_rejected` (async twin `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_manager_that_degrades_to_a_list_is_rejected`), and `examples/fakeshop/test_query/test_list_field_api.py::test_holder_manager_that_drifts_alias_is_rejected`.

Neither helper is public surface, and the cross-module import is a single line. The helpers live in `utils/querysets.py` rather than in either consuming module precisely because more than one field factory needs them: a helper shared by the list field, the connection field and the Relay node defaults belongs at a neutral site, so a change to the coroutine-in-sync rejection contract touches one body.

The two rejected alternatives (inline copies of the helpers; a `list_field.py`-local async-detection mechanism) are in [the rationale companion][spec-020-rationale].

### Decision 4 — Optimizer cooperation

`DjangoListField` does NOT touch the optimizer source code. The cooperation contract is:

- The default resolver returns a `QuerySet` (not a Python `list`).
- The root-gated `DjangoOptimizerExtension.resolve` hook (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.resolve`) fires on `info.path.prev is None`; the field site IS a root (top-level `Query` field), so the hook fires.
- `_optimize` (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize`) unwraps the async-completion adapter the field returns under async execution (`django_strawberry_framework/utils/querysets.py::unwrap_async_queryset_adapter`), then normalizes its input through the shared `django_strawberry_framework/utils/querysets.py::normalize_query_source` (`Manager` → `QuerySet`, non-queryset iterables short-circuit); the field returns a `QuerySet`, so the normalization is a no-op.
- The selection-tree walker (`django_strawberry_framework/optimizer/walker.py`) reads the target `DjangoType` from `_resolve_model_from_return_type(info)` — defined at `django_strawberry_framework/optimizer/extension.py::_resolve_model_from_return_type`, called inside `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension._optimize #"resolved = _resolve_model_from_return_type(info)"`, and returning an `_OriginAndModel` pair (the resolved Strawberry origin plus its model) or `None`. The return-type machinery already handles `list[T]` annotations.
- Plan caching, FK-id elision, `only()` projection, [queryset diffing][glossary-queryset-diffing], strictness mode — all shipped, all apply unchanged.

**Scope narrowing — root only.** The optimizer extension is explicitly root-gated on `info.path.prev is None`. A `DjangoListField` used at a **nested non-root** position on a Strawberry type — for example, a child `@strawberry.type` carrying `more_items: list[ItemType] = DjangoListField(ItemType)` — produces a functional list resolver (the default body still runs and `get_queryset` is still applied), but the optimizer's `resolve` hook does NOT fire because `info.path.prev` is not `None`. The contract is therefore **root list fields only**; nested non-root use works but is not root-optimized (no negative test is owed: the contract is "no promise of optimization there", not "a promise of non-optimization").

`examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_optimized_nested_selection` pins the root-position planning end-to-end with an exact `assertNumQueries(N)` over a nested selection: an exact count is what catches a default resolver that returns an evaluated Python `list` (rows still come back, but the optimizer never engaged), alongside the URL routing + view + schema execution + JSON serialization round trip.

The rejected alternatives (bypassing the root gate, extending the hook to plan nested `DjangoListField` sites, an `info.context` marker) are in [the rationale companion][spec-020-rationale].

### Decision 5 — Validation & error shapes

The `DjangoListField(arg, *, resolver=None, description=None, deprecation_reason=None, directives=(), max_rows=None, trusted_max_rows=False)` constructor validates:

- `arg` is a class (`inspect.isclass(arg)`); otherwise `ConfigurationError("DjangoListField requires a DjangoType class; got <repr>.")`.
- `arg` is `issubclass(arg, DjangoType)`; otherwise `ConfigurationError("DjangoListField requires a DjangoType subclass; got <name>.")`.
- `arg` carries its **own** registered definition — `definition = getattr(arg, "__django_strawberry_definition__", None)` is not `None`, `definition.origin is arg`, **and** `definition is registry.get_definition(arg)` (the registry's exact object, never a copy or a fabricated same-origin definition); otherwise `ConfigurationError("DjangoListField target <name> is not a registered DjangoType. This usually means <name>'s `Meta` is missing a `model` declaration, or it inherits a definition from a parent without declaring its own `Meta`.")`. The attribute is assigned at `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__django_strawberry_definition__ = definition"` only when the `DjangoType` subclass carries a `Meta` with a `model` — but it is **inherited via MRO**, so `hasattr(...)` is NOT a sufficient discriminator: it would accept a subclass that omits its own `Meta` and bind the field to a target whose definition, `Meta.primary` state and model all belong to the parent. The own-class-origin identity check is the invariant (`tests/test_list_field.py::test_djangolistfield_rejects_djangotype_subclass_without_own_meta`), and the registry-identity check closes a definition object that merely claims the origin (`tests/test_list_field.py::test_djangolistfield_rejects_a_fabricated_same_origin_definition`, `::test_djangolistfield_rejects_a_copy_of_the_real_definition`).
- `resolver`, when supplied, is callable; otherwise `ConfigurationError("DjangoListField resolver must be callable.")`.

The four target checks above are ordered among themselves, and that order is load-bearing — each one assumes the previous passed. They are shared, not local to this factory: see [Decision 1](#decision-1--module-location-mechanism--public-export).

The row-bound guards run **first**, ahead of all four target checks: a `max_rows` that is not a positive integer is rejected by `django_strawberry_framework/resource_policy.py::validate_collection_bound`, and a `trusted_max_rows` that is not exactly `True` or `False` by `django_strawberry_framework/resource_policy.py::validate_trusted_flag`, before the target is inspected, so a field constructed with both a bad target and a bad `max_rows` reports the `max_rows` error (`tests/test_list_field.py::test_djangolistfield_rejects_a_non_positive_max_rows_at_construction`, `tests/test_list_field.py::test_a_list_field_trusted_max_rows_opt_in_must_be_exactly_boolean`). What the bound then means is [Row bound](#row-bound); `examples/fakeshop/test_query/test_list_field_api.py::test_holder_untrusted_max_rows_is_the_limit_ceiling` pins the narrowing.

After the target checks, `directives=` is read through `django_strawberry_framework/utils/directives.py::validated_field_directives`: a bare string or bytes value, or one that cannot be iterated, raises `ConfigurationError` (`tests/test_list_field.py::test_djangolistfield_rejects_bare_string_directives`, `::test_djangolistfield_rejects_non_iterable_directives`).

Error sites in the `DjangoListField` constructor: the row-bound guards, the shared target-validation guards, and the directives guard, in that order. All errors raise [`ConfigurationError`][glossary-configurationerror]. Every message opens with the factory name; the non-class, non-subclass and trusted-flag arms end `; got <repr>.`

Validation fires in the constructor rather than at type-decoration or [`finalize_django_types()`][glossary-finalize-django-types] time: the rules are local to the constructor, no cross-class state is needed, and the error surfaces at the line that wrote `DjangoListField(...)`. This is symmetric with [`OptimizerHint`][glossary-optimizerhint]-related `Meta` validation, which fires at type creation.

The deferred-validation and model-class-argument alternatives, and why each lost, are in [the rationale companion][spec-020-rationale].

### Decision 6 — `Meta.primary` interaction

`DjangoListField(TargetType)` takes a concrete `DjangoType` subclass as its argument — never a model class. This means:

- For a model with one `DjangoType` and no `Meta.primary` declaration — `DjangoListField(TargetType)` is unambiguous and works.
- For a model with multiple `DjangoType`s where one carries `Meta.primary = True` — `DjangoListField(PrimaryType)` and `DjangoListField(SecondaryType)` both work; each is bound to the explicit target's queryset, `get_queryset` hook, and (if any) optimizer hints. No registry lookup happens.
- For a model with multiple `DjangoType`s where the primary ambiguity hasn't been resolved (no `Meta.primary` declared on any) — `finalize_django_types()` raises `ConfigurationError` ([`spec-018-meta_primary-0_0_6.md`][spec-018] Decision 5); `DjangoListField` is downstream and inherits the same loud failure mode.

`DjangoListField(PrimaryType)` and `DjangoListField(SecondaryType)` produce two distinct optimizer [plan cache][glossary-plan-cache] entries, because plan-cache keys include the resolver's origin Strawberry type - pointing two fields at two types on one model carries no cache-poisoning risk. The explicit-target shape is the same one the relation-resolver paths use for multi-type-per-model targets ([`docs/GLOSSARY.md#metaprimary`][glossary-metaprimary]).

Pinned by `examples/fakeshop/test_query/test_list_field_api.py::test_holder_list_field_uses_the_named_targets_queryset`, parametrized over a field pointed at the primary `PatronType` and one pointed at the secondary `PublicPatronType`: the named target's `get_queryset` runs, the other type's does not.

The rejected alternatives (accepting a model class and looking up the primary, defaulting to the primary on an ambiguous model, a `DjangoListField.for_model(Model)` classmethod) are in [the rationale companion][spec-020-rationale].

### Decision 7 — Scope boundary vs relation list fields

`DjangoListField` is the **root** primitive — it adds a new list-shape field to a `Query` class (or any `@strawberry.type` class). It is NOT the relation-side many-list field; that path is already shipped via generated relation resolvers (see [`docs/GLOSSARY.md#relation-handling`][glossary-relation-handling]):

> reverse `ForeignKey` → `list[target_type]`. The optimizer plans `prefetch_related`. Many-side resolvers return Python lists, not Django managers.

`DjangoListField` does NOT:

- Replace the generated relation resolvers with `DjangoListField`-based plumbing.
- Change the shape of many-side relation fields (still `list[T]`, still returned as Python lists from generated resolvers).
- Auto-upgrade reverse-FK / M2M fields to use `DjangoListField`.

Unifying the two belongs to the connection subsystem (`DONE-030-0.0.9`), not this spec.

Why the root primitive and the generated relation-side many-list resolvers stay separate is in [the rationale companion][spec-020-rationale].

### Decision 8 — Out-of-scope boundary with `DjangoConnectionField`

`DjangoListField` and `DjangoConnectionField` ([`DONE-030-0.0.9`][kanban]) are sibling primitives. Both bind to a `DjangoType`; both apply `cls.get_queryset(...)`; both cooperate with the optimizer.

Boundary line:

- `DjangoListField` returns `list[T!]!` (or `list[T!]`); no cursors, no edges, no `pageInfo`, no Relay arguments — **and no order guarantee**. The default resolver appends no tiebreaker, so row order is whatever the database returns unless the query supplies an `orderBy` argument or the model declares `Meta.ordering`.
- `DjangoConnectionField` returns a [`DjangoConnection`][glossary-djangoconnection] (`Connection[T]`) with `edges` / `node` / `pageInfo` / `totalCount` and Relay pagination arguments (`first` / `after` / `last` / `before`), **and a pk tiebreaker appended to guarantee a deterministic total order** — its positional cursors require one.
- The ordering asymmetry between the two primitives is deliberate, not an oversight: a flat list has no cursors that an unstable order could invalidate, so paying for a tiebreaker on every list query would buy nothing. A consumer who needs deterministic list order declares `Meta.ordering` on the model or passes `orderBy`.
- Filter / order / search / aggregate input arguments belong to the relevant Layer-3 spec for each primitive; the list field's `offset` / `limit` / `orderBy` surface is [`spec-050`][spec-050]'s.

A consumer migrating from `DjangoListField` to `DjangoConnectionField` later:

```diff
- all_branches: list[BranchType] = DjangoListField(BranchType)
+ all_branches: DjangoConnection[BranchType] = DjangoConnectionField(BranchType)
```

Same `DjangoType` argument; same `get_queryset` cooperation; same optimizer integration; richer return shape.

The rejected alternatives (a single `DjangoField` symbol with a `connection=True/False` argument; inheriting `DjangoConnectionField` from `DjangoListField`) are in [the rationale companion][spec-020-rationale].

### Decision 9 — Example-app migration posture

`examples/fakeshop/apps/library/schema.py`'s `Query` class carries the `DjangoListField` root fields beside the hand-written resolvers, replacing none: `all_library_branches_via_list_field: list[BranchType] = DjangoListField(BranchType)` for the default-resolver path, `all_library_branches_via_list_field_nullable: list[BranchType] | None` for the nullable-outer rendering, and `all_library_branches_via_list_field_manager_resolver` for a consumer resolver returning a `Manager`. The hand-written `all_library_*` resolvers stay hand-written (`all_library_branches`'s `order_by("id")` is depended on by `test_library_relation_override_shapes_http_response_data` in `examples/fakeshop/test_query/test_library_api.py`, which seeds two branches and asserts a deterministic order. `Branch` has no model-level `Meta.ordering`, so the default-manager queryset is unordered).

Two constraints on the surrounding resolvers:

- The hand-written `all_library_*` resolvers carry `order_by("id")` for deterministic test ordering.
- The `all_library_prefetched_books` resolver uses `Book.objects.select_related("shelf").prefetch_related("genres").order_by("id")` - a consumer-shaped queryset. That resolver MUST stay a hand-rolled `@strawberry.field` so it keeps exercising the optimizer's [queryset diffing][glossary-queryset-diffing] path: the consumer's `prefetch_related("genres")` suppresses the plan's own, and when `shelf` is selected the consumer JOIN is released because `ShelfType` declares a custom `get_queryset`, so the plan's `shelf` `Prefetch`, scoped by that hook, is the only source of shelf rows.

The replacement postures considered and rejected are in [the rationale companion][spec-020-rationale].

### Decision 10 — Joint `0.0.7` cut

`0.0.7` is one release carrying seven cards: `DONE-020-0.0.7` (this card), `DONE-021-0.0.7` (`apps.py`), `DONE-022-0.0.7` (schema-export management command), `DONE-023-0.0.7` (multi-db cooperation contract), `DONE-024-0.0.7` (Django Trac #37064 hardening), `DONE-025-0.0.7` (warning-free scalar registration) and `DONE-026-0.0.7` (scalar conversion end-to-end coverage). The release has one version bump — `django_strawberry_framework/__init__.py` `__version__` (the single version source) and the pinned assertion in `tests/base/test_init.py` — owned by whichever card in the bundle ships last, not by each card. There is no separate release-cut card in `KANBAN.md`; the policy names the owner rather than a card.

The rejected alternatives (each card bumping independently; blocking every card on one integration commit) are in [the rationale companion][spec-020-rationale].

## Implementation plan

Six slices aligned with the [Slice checklist](#slice-checklist); Slice 0 records the Strawberry facts the factory-function design rests on and carries no repo code.

| Slice | Files | Tests |
| --- | --- | --- |
| 0 — Strawberry facts | (none) | (none) |
| 1 — Module + factory function | `django_strawberry_framework/list_field.py`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py` | the `__all__` pin |
| 2 — Validation | `django_strawberry_framework/list_field.py`, `tests/test_list_field.py` | the validation-guard tests |
| 3 — Optimizer + `get_queryset` cooperation | `examples/fakeshop/test_query/test_list_field_api.py`, `examples/fakeshop/test_query/test_list_field_async_api.py` | the behavior tests named in [Test plan](#test-plan) |
| 4 — Live HTTP coverage | `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py` | the `all_library_branches_via_list_field*` HTTP tests |
| 5 — Docs and board | `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md` | (none) |

## Edge cases and constraints

- **`Meta.primary` ambiguity not resolved at the registry**. `DjangoListField(TargetType)` accepts an explicit `DjangoType` so the registry's primary/secondary state is irrelevant at the field site. If `finalize_django_types()` later raises a `Meta.primary` ambiguity error for the target's model, that error is the one consumers see — not a `DjangoListField`-specific one.
- **Custom managers via `Meta.default_manager_name`**. Django's `_default_manager` honors the model's `default_manager_name` if set; `DjangoListField` inherits this for free. No special-casing.
- **`null=True` on the row's primary key**. Django does not allow nullable single-column primary keys on normal models; the `DjangoListField` resolver path does not introspect the pk.
- **Model proxies**. Django proxy models share the underlying table; `_default_manager.all()` returns proxy instances. `DjangoListField` works the same way it does for the base model; the consumer just passes the proxy-backed `DjangoType`.
- **Abstract `DjangoType` bases without a `Meta`**. The validation in [Decision 5](#decision-5--validation--error-shapes) catches this via the "registered DjangoType" check — abstract bases don't have `__django_strawberry_definition__` and raise `ConfigurationError` at construction.
- **Multi-database routing**. `model._default_manager.all()` is routed by Django's database router automatically, the same `Manager.all()` routing the multi-db cooperation contract (`DONE-023-0.0.7`) covers for relations.
- **[Strictness mode][glossary-strictness-mode] and N+1 detection**. The optimizer's strictness mode operates at the relation-walk level, not the root-resolver level. `DjangoListField`-served root querysets pass through the strictness contract unchanged (`examples/fakeshop/test_query/test_list_field_api.py::test_cascaded_item_list_stays_silent_under_strictness_raise`).
- **Sync and async execution**. The field works under both synchronous and asynchronous GraphQL execution; the default resolver's runtime `async_execution()` branch handles both. Pinned by the sync live suite (`examples/fakeshop/test_query/test_list_field_api.py`) beside its async twin (`examples/fakeshop/test_query/test_list_field_async_api.py::test_async_queryset_completion_default_resolver`).
- **`functools.partial`-wrapped and callable-object async consumer resolvers work.** `inspect.iscoroutinefunction(functools.partial(some_async_fn, ...))` returns `False`, and so does `inspect.iscoroutinefunction(instance)` for an instance whose `__call__` is `async def` — which is exactly why neither is the predicate the factory uses. Construction-time detection routes through `django_strawberry_framework/utils/typing.py::is_async_callable`, the wrapper-aware superset of `inspect.iscoroutinefunction`, so every spelling that predicate covers builds the async wrapper and its `Manager`/`QuerySet` return receives `get_queryset` — the two above, a raw `staticmethod async def` descriptor (`examples/fakeshop/test_query/test_list_field_async_api.py::test_async_http_staticmethod_resolver_still_applies_visibility`), and any nesting of the two wrapper kinds. No consumer rewrapping is needed:

  ```python path=null start=null
  # WORKS -- is_async_callable sees through the partial, so DjangoListField
  # builds an async _wrap and BranchType.get_queryset(...) is applied to the
  # awaited return value.
  field = DjangoListField(
      BranchType,
      resolver=functools.partial(my_async_resolver, some_arg=1),
  )

  # WORKS -- an async generator function is a sync callable returning an
  # async-only iterable; the sync arm routes it to the async-iterable path.
  field = DjangoListField(BranchType, resolver=my_async_generator_resolver)
  ```

  The factory carries no runtime-coroutine fallback, and needs none: a resolver detected as sync that nonetheless returns a coroutine, a custom awaitable, or a `Future` is rejected loudly rather than passed through with the hook skipped (`examples/fakeshop/test_query/test_list_field_async_api.py::test_async_http_rejects_a_sync_resolver_that_returns_a_coroutine`, `::test_async_http_rejects_a_sync_resolver_that_returns_a_custom_awaitable`, `tests/test_list_field.py::test_djangolistfield_sync_resolver_returning_future_cancels_it`). An async-only iterable returned from a sync-detected resolver is routed to the async-iterable arm instead ([Decision 2](#decision-2--default-resolver-shape)).

## Test plan

Tests live in the package tree and the live tier, per [`docs/TREE.md`][tree] and [`AGENTS.md`][agents]: a behavior a real query reaches is pinned over `/graphql/`, and `tests/test_list_field.py` keeps only what no request can express.

### `tests/test_list_field.py`

Package tests; system-under-test is `django_strawberry_framework`. The file is the flat module's mirror. The list below names the contract pins this spec owes; the file also carries the argument-surface, async-iterable, row-bound and sealed-boundary pins, so it is not an inventory of the file.

Validation tests (Slice 2):

- `test_djangolistfield_rejects_non_class_argument` — passing a string, int, instance, etc., raises `ConfigurationError`.
- `test_djangolistfield_rejects_non_djangotype_class` — passing a plain class that doesn't subclass `DjangoType` raises `ConfigurationError`.
- `test_djangolistfield_rejects_djangotype_without_definition` — passing an abstract `DjangoType` base without a `Meta` raises `ConfigurationError`.
- `test_djangolistfield_rejects_djangotype_subclass_without_own_meta` — an inherited definition does not count as the subclass's own.
- `test_djangolistfield_rejects_a_fabricated_same_origin_definition` / `test_djangolistfield_rejects_a_copy_of_the_real_definition` — only the registry's exact definition object is accepted.
- `test_djangolistfield_rejects_non_callable_resolver` — `resolver="not callable"` raises `ConfigurationError`.
- `test_djangolistfield_rejects_a_non_positive_max_rows_at_construction` — the row-bound guard runs first.
- `test_a_list_field_trusted_max_rows_opt_in_must_be_exactly_boolean` — `trusted_max_rows=` accepts only an exact `bool`.
- `test_djangolistfield_rejects_bare_string_directives` / `test_djangolistfield_rejects_non_iterable_directives` — `directives=` must be a sequence of directive instances.

### Live tier

Behavior tests (Slice 3), each over `/graphql/` (sync) or `/graphql-async/` (async):

- `examples/fakeshop/test_query/test_library_api.py::test_branches_via_list_field_default_resolver_applies_get_queryset_live` — the default resolver routes the queryset through `BranchType.get_queryset`, which hides `city="restricted"` branches from the anonymous client.
- `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_get_queryset_is_awaited` — an `async def get_queryset(...)` is awaited by the default resolver under async execution.
- `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_queryset_completion_default_resolver` — the default resolver completes under async execution; the sync live suite covers the synchronous side.
- `examples/fakeshop/test_query/test_list_field_api.py::test_shipped_branches_sync_http_rejects_an_async_get_queryset` — the sync view refuses an async `get_queryset` with `SyncMisuseError` instead of skipping visibility (`django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync #"result = reject_async_in_sync_context("`).
- `examples/fakeshop/test_query/test_list_field_api.py::test_holder_a_query_source_resolver_still_applies_target_visibility` — a **sync** `resolver=` returning a `QuerySet` or a `Manager` still runs `BranchType.get_queryset`.
- `examples/fakeshop/test_query/test_list_field_api.py::test_holder_a_materialized_list_skips_target_visibility` — a **sync** `resolver=` returning a Python `list` passes through without `get_queryset`.
- `examples/fakeshop/test_query/test_list_field_async_api.py::test_async_http_classified_resolver_still_applies_visibility` / `::test_async_a_materialized_list_skips_target_visibility` — the async-callable `resolver=` twins: the wrapper awaits the consumer coroutine BEFORE the `isinstance` check, so a queryset return still runs `get_queryset` and a Python-`list` return passes through; `::test_async_a_query_source_resolver_still_applies_target_visibility` covers a sync resolver under async execution.
- `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_optimized_nested_selection` — root-position planning with an exact `assertNumQueries(N)`; the docstring derives `N` from the selection shape.
- `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_nullable_outer_renders_and_resolves` — a `list[BranchType] | None` field renders `[BranchType!]` and resolves over the wire.
- `examples/fakeshop/test_query/test_list_field_api.py::test_shipped_branches_introspection_return_types` — the bare `list[BranchType]` annotation renders `[BranchType!]!`.
- `examples/fakeshop/test_query/test_list_field_api.py::test_holder_membership_card_list_elides_patron_id_to_one_query` — an id-only forward relation on a list field uses the source FK column alone (FK-id elision).
- `examples/fakeshop/test_query/test_list_field_api.py::test_holder_list_field_uses_the_named_targets_queryset` — see [Decision 6](#decision-6--metaprimary-interaction).
- `examples/fakeshop/test_query/test_library_api.py::test_library_branches_via_djangolistfield_consumer_manager_resolver_over_http` — a consumer resolver returning a `Manager` over the shipped schema.

The HTTP test files' reload pattern (clear the global registry, reload app schema modules, then reload the project schema and URLconf) is preserved.

## Doc updates

- [`docs/GLOSSARY.md`][glossary] — [`DjangoListField`][glossary-djangolistfield] reads `shipped (0.0.7)`; its body describes the factory function, the class-attribute annotation driving outer nullability, the default `model._default_manager.all()` resolver, `cls.get_queryset(...)` applied in sync + async contexts AND to consumer-resolver `Manager`/`QuerySet` returns (graphene-django parity), and root-only optimizer cooperation; [Public exports][glossary-public-exports] and the Index table list it.
- [`README.md`][readme] and [`docs/README.md`][docs-readme] — `DjangoListField` among the shipped surface.
- [`docs/TREE.md`][tree] — `list_field.py` and `tests/test_list_field.py`; one home for the symbol.
- [`GOAL.md`][goal] — the `graphene-django` migration story names `DjangoListField` with no shape change at the migration site.
- [`TODAY.md`][today] — `DjangoListField` among the demonstrated capabilities, never on a wait-for list.
- [`KANBAN.md`][kanban] — the `DONE-020-0.0.7` card in add-only language.
- [`CHANGELOG.md`][changelog] — the `[0.0.7]` `### Added` entry: `DjangoListField` — non-Relay `list[T]` field for **root Query fields**, with default `model._default_manager.all()` resolver, `cls.get_queryset(...)` cooperation in sync + async contexts and on consumer-resolver `Manager`/`QuerySet` returns (graphene-django parity), optimizer cooperation via root-gating, outer nullability driven by the consumer's class-attribute annotation, and standard field-level metadata pass-through (`description`, `deprecation_reason`, `directives`).

## Out of scope (explicitly tracked elsewhere)

- `DjangoConnectionField` and Relay-shaped pagination: `DONE-030-0.0.9` in [`KANBAN.md`][kanban].
- [`DjangoNodeField`][glossary-djangonodefield] (root-level Relay node lookup): `DONE-030-0.0.9`.
- The `offset` / `limit` / `orderBy` argument surface: [`spec-050`][spec-050], `DONE-050-0.0.15`.
- Filter / search / aggregate input arguments on the field: `DONE-027-0.0.8` / `TODO-BETA-047-0.1.2` / `TODO-BETA-049-0.1.3`.
- Cascade permissions and field-level permissions: `DONE-034-0.0.10`.
- [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning]: `DONE-033-0.0.9`.
- Multi-database / sharding-aware queryset routing: cooperation contract `DONE-023-0.0.7`; first-class sharding-aware planning post-`1.0.0` in [`BACKLOG.md`][backlog].
- Auto-upgrade of reverse-FK / M2M relation fields to `DjangoListField`-based plumbing: deferred indefinitely; see [Decision 7](#decision-7--scope-boundary-vs-relation-list-fields).
- Cursor pagination on `DjangoListField`: the connection field's responsibility. Row **limits** are the opposite of out of scope — every `DjangoListField` is row-bounded (see [Row bound](#row-bound)).

## Definition of done

1. `django_strawberry_framework/list_field.py` defines `DjangoListField` as a factory function per [Decision 1](#decision-1--module-location-mechanism--public-export) and [Decision 2](#decision-2--default-resolver-shape) — returns the value of `strawberry.field(resolver=..., description=..., ...)`; closure-captures `target_type`; the wrapper's published signature is synthesized (`root`, `info: strawberry.types.Info`, plus [`spec-050`][spec-050]'s list arguments; no catch-all `**kwargs` is published, because Strawberry treats every parameter as a GraphQL argument). Sync callables, async callables (every shape `django_strawberry_framework/utils/typing.py::is_async_callable` covers: `async def`, an `async def __call__` instance, a raw `staticmethod` descriptor, and nestings of `functools.partial` / `staticmethod` over those) and async generator functions are all supported as consumer resolvers, the wrapper shape chosen at construction time by `is_async_callable`, with the sync arm routing an async-only iterable return at call time; there is no runtime-coroutine fallback, and a sync-detected resolver returning a coroutine / awaitable / `Future` is rejected loudly instead.
2. `django_strawberry_framework/__init__.py` re-exports `DjangoListField` and includes it in `__all__` in alphabetical position.
3. `tests/base/test_init.py`'s `__all__` assertion includes `"DjangoListField"`.
4. `tests/test_list_field.py` contains the validation tests listed in the [Test plan](#test-plan); the behavior tests are at the live tier.
5. `examples/fakeshop/apps/library/schema.py` carries the root fields named in [Decision 9](#decision-9--example-app-migration-posture) beside the hand-written `all_library_*` resolvers.
6. `examples/fakeshop/test_query/test_library_api.py` asserts the `DjangoListField`-served field's `/graphql/` response, its exact query count, and its `get_queryset` application.
7. Constructor-time validation rejects a non-class, a non-`DjangoType`, a subclass carrying no registered definition of its **own** (an inherited, copied or fabricated one does not count), and a non-callable `resolver=`, with `ConfigurationError`s matching the message contract in [Decision 5](#decision-5--validation--error-shapes); a non-positive `max_rows=`, a non-`bool` `trusted_max_rows=` and an unreadable `directives=` are rejected at the same site.
8. The default resolver returns a `QuerySet` (not a Python `list`; under async execution, the queryset inside the async-completion adapter) so the root-gated `DjangoOptimizerExtension` plan applies at the root. The queryset is row-bounded per [Row bound](#row-bound), and the bound is applied by slicing after the visibility hook and any consumer post-processing, so a `QuerySet` carries it into SQL as a `LIMIT`.
9. The sync path rejects an async `cls.get_queryset` with `SyncMisuseError`, the `ConfigurationError` subclass that `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` raises for every read surface.
10. The async path awaits the `get_queryset` coroutine and applies the optimizer through the same root-gated hook.
11. A consumer-supplied `resolver=` runs in place of the default body. When the consumer return value is a `Manager` or `QuerySet`, `target_type.get_queryset(qs, info)` is applied (graphene-django parity); a Python-`list` return passes through unchanged; an async-only iterable (an async generator, or an `AsyncIterable` from a sync-detected resolver) is bounded under async execution and rejected with `SyncMisuseError` under sync execution. Every path is pinned by tests.
12. Outer-list nullability is driven by the consumer's class-attribute annotation: `list[T]` → `[T!]!`, `list[T] | None` → `[T!]`. Both renderings are pinned by schema-introspection tests.
13. The contract is **root list fields only**. Nested non-root usage is functional but not root-optimized. The CHANGELOG and GLOSSARY entries reflect this scope.
14. `Meta.primary` interaction is covered: a model with multiple `DjangoType`s, one declared primary, is queryable through `DjangoListField(PrimaryType)` AND `DjangoListField(SecondaryType)` independently per [Decision 6](#decision-6--metaprimary-interaction).
15. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`).
16. `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `GOAL.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` reflect the shipped state per the [Doc updates](#doc-updates) section.
17. `KANBAN.md`'s `DONE-020-0.0.7` body uses **add-only language**: the field was added beside the hand-written `all_library_*` resolvers, replacing none.
18. The version bump follows [Decision 10](#decision-10--joint-007-cut): one bump for the `0.0.7` release, owned by the last card to ship.
19. One public export (`DjangoListField`) belongs to this spec.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[backlog]: ../../BACKLOG.md
[changelog]: ../../CHANGELOG.md
[contributing]: ../../CONTRIBUTING.md
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[spec-050]: ../spec-050-list_field_arguments-0_0_15.md
[glossary-apply-cascade-permissions]: ../GLOSSARY.md#apply_cascade_permissions
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnection]: ../GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-fk-id-elision]: ../GLOSSARY.md#fk-id-elision
[glossary-get-queryset-visibility-hook]: ../GLOSSARY.md#get_queryset-visibility-hook
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-only-projection]: ../GLOSSARY.md#only-projection
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-plan-cache]: ../GLOSSARY.md#plan-cache
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-relation-handling]: ../GLOSSARY.md#relation-handling
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-strictness-mode]: ../GLOSSARY.md#strictness-mode
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-015]: spec-015-relay_interfaces-0_0_5.md
[spec-018]: spec-018-meta_primary-0_0_6.md
[spec-020-rationale]: appx/spec-020-list_field-0_0_7-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
