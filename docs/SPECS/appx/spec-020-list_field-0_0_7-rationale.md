# Rationale: spec-020 — `DjangoListField` (non-Relay list) (reasons and rejected alternatives)

Companion to [`spec-020-list_field-0_0_7.md`][spec-020]. The spec is the contract; this file holds, per Decision, why the code is shaped the way it is and the alternatives that lost.

## Entries keyed to the spec

### [Decision 1 — Module location, mechanism, & public export][spec-020-d1]

**Why `list_field.py`.** `docs/TREE.md` places a single-file subsystem as a flat module at the package root, and the flat module pairs with `tests/test_list_field.py` by the `tests/test_<module>.py` mirror rule. `connection.py` holds the Relay connection field, a richer API (edges, `pageInfo`, cursors); putting both primitives there would mix two return-shape contracts in one module.

**Why the target guards live here.** `list_field.py::_validate_djangotype_target` and `::_validate_relay_djangotype_target` are imported by `connection.py` and `relay.py`, so "registered target" means one thing at every field entry point and a guard change lands once.

**Rejected alternatives.**

- **Inline into `__init__.py`.** `__init__.py` is a re-export hub, not a module body.
- **A `fields/` subpackage with `fields/list_field.py`.** A single file is a flat module; subpackages are for multi-module subsystems.
- **Subclass `strawberry.field`.** Not viable: `strawberry.field` is a function, not a class.
- **A descriptor class whose `__set_name__` returns a `StrawberryField`.** Not viable: `__set_name__` cannot replace the already-assigned class attribute with its return value. Strawberry discovers fields in `@strawberry.type`'s class-body walk, which converts the `StrawberryField` that `strawberry.field(...)` returns; a factory returning that value needs no descriptor protocol.
- **Relocate the target guards to `utils/`.** Three factories import them from `list_field.py`; the list field is the base case the Relay variant extends.

### [Decision 2 — Default resolver shape][spec-020-d2]

**Why this shape.** `model._default_manager.all()` matches graphene-django (`graphene_django/fields.py::DjangoListField.get_manager`) and the package's own seed (`django_strawberry_framework/utils/querysets.py::base_queryset`). `cls.get_queryset(qs, info)` is the load-bearing visibility hook, so the field applies it to every queryset-shaped return, default or consumer. Returning a `QuerySet` rather than a `list` is what lets the root-gated optimizer plan apply.

**Rejected alternatives.**

- **Default resolver returns an evaluated Python `list`.** `django_strawberry_framework/utils/querysets.py::normalize_query_source` short-circuits a non-queryset, so the optimizer would pass a `list` through unplanned and every nested relation would N+1.
- **Skip `cls.get_queryset` on consumer-resolver returns.** graphene-django applies `get_queryset` to consumer-resolver `QuerySet` returns too; skipping it would weaken the visibility hook and break the parity the field claims. A consumer who wants the bypass returns a Python `list`.
- **A `nullable_list=` constructor argument.** Strawberry already reads the class-attribute annotation, so the kwarg would fight or silently override it, and honoring it would mean constructing a `StrawberryField` directly instead of going through `strawberry.field(...)`. The consumer expresses it with `| None`.
- **A first-positional `(type_cls, info)` resolver signature.** Strawberry calls resolvers with `(root, info)`; the target type comes from closure, the same shape as graphene-django's `partial(self.list_resolver, django_object_type, …)`.
- **Publishing a catch-all `**kwargs`.** Strawberry treats every published parameter as a GraphQL argument: an annotated `**kwargs: Any` becomes an argument named `kwargs` and fails schema construction, and an unannotated parameter raises `MissingArgumentsAnnotationsError`. The wrappers accept `*args` / `**kwargs` internally, and `_synthesized_list_signature` publishes only `root`, `info` and the named list arguments.
- **`null=True` item types.** Django querysets never yield `None` rows, so `list[T | None]` is meaningless at the resolver layer.
- **A runtime `inspect.iscoroutine(result)` fallback in the sync wrapper.** A plain `def` resolver that returns an awaitable is committed to the sync path; awaiting it there is not possible, and passing it through would skip `get_queryset`. `django_strawberry_framework/utils/querysets.py::reject_awaitable_sync_source` rejects it with `SyncMisuseError` instead, and construction-time `is_async_callable` covers the wrapper spellings that `inspect.iscoroutinefunction` misses.

### [Decision 3 — `get_queryset` and async symmetry][spec-020-d3]

**Why `utils/querysets.py`.** `apply_type_visibility_sync` / `apply_type_visibility_async` are shared by every recomposing read surface (the Relay node defaults, the connection root, this field, the cascade, filters, the optimizer walker, mutation resolvers), so the coroutine-in-sync rejection and the sealed boundary have one body.

**Why the seal belongs to this Decision.** Sealing is a property of how the visibility hook is applied, not of optimizer cooperation; a reader consulting the hook contract finds it here.

**Rejected alternatives.**

- **Inline copies of the visibility helpers in `list_field.py`.** Two sources of truth for the coroutine-in-sync rejection contract.
- **A `list_field.py`-local async-detection mechanism.** It would fork `django_strawberry_framework/utils/execution_mode.py::async_execution`, the predicate the Relay defaults use, and the suite would validate one contract twice.

### [Decision 4 — Optimizer cooperation][spec-020-d4]

**Why no optimizer code.** The optimizer's contract is "give me a `QuerySet` at the root; I'll walk the selection tree once", so a primitive that returns a `QuerySet` inherits every optimizer feature.

**Why an exact query count.** `assertNumQueries(N)` with `N` derived in the test docstring catches a default resolver that returns an evaluated `list`: rows still come back, but the optimizer never engaged. A permissive bound or SQL-string sniffing would let that slide.

**Rejected alternatives.**

- **Bypass the root gate for `DjangoListField`.** Nothing to bypass: the gate already fires at the root.
- **Extend the optimizer hook to plan nested `DjangoListField` sites.** An optimizer change outside this field's scope; nested non-root use is functional and carries no optimization promise.
- **A `DjangoListField`-specific marker on `info.context`.** Unnecessary: `_resolve_model_from_return_type` already identifies the target type from the return annotation.

### [Decision 5 — Validation & error shapes][spec-020-d5]

**Why the constructor.** The rules are local and need no cross-class state, and failing at construction puts the error on the line that wrote `DjangoListField(...)`, which is easier to localize than a later `finalize_django_types()` error.

**Why own-origin plus registry identity, not `hasattr`.** `__django_strawberry_definition__` is inherited via MRO, so `hasattr` would accept a subclass with no `Meta` of its own and bind the field to the parent's definition, `Meta.primary` state and model. The registry-identity check closes a definition object that merely claims the origin. A guard documented as looser than it is invites a later reader to simplify it back.

**Why the row-bound guards run first.** They inspect only the field's own arguments, so they report before any target introspection.

**Rejected alternatives.**

- **Defer validation to `finalize_django_types()`.** A consumer does not necessarily call it before expecting `DjangoListField(...)` to work or fail, and delayed errors are harder to localize.
- **Accept a model class instead of a `DjangoType`.** With `Meta.primary`, model → `DjangoType` lookup is ambiguous when several types share a model; the explicit type side-steps it (see Decision 6).

### [Decision 6 — `Meta.primary` interaction][spec-020-d6]

**Why the explicit target.** It is what the relation-resolver paths already do for multi-type-per-model targets, and plan-cache keys include the resolver's origin Strawberry type, so a primary-return and a secondary-return field never share a cached plan.

**Rejected alternatives.**

- **Accept a model class and look up the primary `DjangoType`.** Needs a registry call at construction time and makes the field implicitly subject to `Meta.primary` changes.
- **Default to the primary when an ambiguous model is passed.** Same brittleness; the explicit target is unambiguous.
- **A `DjangoListField.for_model(Model)` classmethod.** `DjangoListField(MyType)` is the canonical form and matches graphene-django's `DjangoListField(_type)`.

### [Decision 7 — Scope boundary vs relation list fields][spec-020-d7]

Generated relation many-side resolvers are shipped and tested, so rebuilding them on `DjangoListField` is a refactor with no consumer-visible benefit. The two coexist because they target different call sites: a root `Query` attribute versus a generated relation resolver.

### [Decision 8 — Out-of-scope boundary with `DjangoConnectionField`][spec-020-d8]

**Rejected alternatives.**

- **One `DjangoField` symbol with a `connection=True/False` argument.** The return shapes differ (`list[T]` versus `Connection[T]`), so one symbol would carry two return-type contracts selected by a boolean.
- **Inherit `DjangoConnectionField` from `DjangoListField`.** The connection's output machinery (edges, `pageInfo`) does not compose as a subclass. The two share helpers instead (the visibility helpers in `utils/querysets.py`, the target validators in `list_field.py`) without an inheritance relationship.

### [Decision 9 — Example-app migration posture][spec-020-d9]

**Why add rather than replace.** Sibling fields leave the hand-written resolvers and their HTTP-test ordering dependencies untouched while exercising the default resolver, the nullable-outer rendering and the consumer-`Manager` path in isolation.

**Rejected alternatives.**

- **Replace `all_library_branches` with `DjangoListField(BranchType)`.** Drops `order_by("id")` and breaks `test_library_relation_override_shapes_http_response_data`'s ordering assertions; `Branch` declares no `Meta.ordering`.
- **Replace it with `DjangoListField(BranchType, resolver=...)` returning `Branch.objects.order_by("id")`.** The field would exercise the consumer-override path instead of the default path, which is the one the example exists to cover.
- **Add `Meta.ordering = ("id",)` to `Branch`.** Changes every `Branch` query in the suite (admin, services, schema execution, HTTP).
- **Replace every hand-written `all_library_*` resolver.** Churn that pins the contract no harder than one addition does.
- **Host the example in `products`.** Every `products` root field is a `DjangoConnectionField`; the app is Relay-shaped by design.

### [Decision 10 — Joint `0.0.7` cut][spec-020-d10]

**Why one bump.** Each card lands self-contained code, tests and docs; the bump is the release's cut-over signal, and the `[0.0.7]` `### Added` entries accumulate under one heading.

**Rejected alternatives.**

- **Each card bumps independently.** The cards merge in arbitrary order, so per-card bumps would compete for one version.
- **Block every card on one integration commit.** The cards lose independence and the review surface balloons.

### `## Borrowing posture`

- **Same symbol name.** Migrants searching for the primitive they already use find it under the same import name.
- **The manager → visibility-hook default** is what a reader expects from "list field for a `DjangoType`".
- **Two `Manager` coercions coexist.** The field wrapper coerces before `get_queryset` so the hook receives a `QuerySet` for every `Model.objects` return; the optimizer's `normalize_query_source` is the safety net for root resolvers that are not `DjangoListField`.

### `## User-facing API`

- **Metadata pass-through** (`description`, `deprecation_reason`, `directives`) makes the field feature-comparable with `strawberry.field(...)`, so a consumer never falls back to a hand-rolled `@strawberry.field` to attach a description.
- **The async spellings defer to `is_async_callable`.** The predicate is the authority; the spec spells the shapes out only where a consumer must recognize their own code.
- **Row bound.** The spec states what the field's two constructor arguments do; [the glossary entry][glossary-djangolistfield] is the consumer-facing authority for how bound and policy compose.

### `## Non-goals`

`DjangoConnectionField` is its own card (`DONE-030-0.0.9`) because its surface (edges, `pageInfo`, Relay pagination arguments, connection-aware planning under `DONE-033-0.0.9`) is much larger than a flat list's.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangolistfield]: ../../GLOSSARY.md#djangolistfield

<!-- docs/SPECS/ -->
[spec-020-d1]: ../spec-020-list_field-0_0_7.md#decision-1--module-location-mechanism--public-export
[spec-020-d10]: ../spec-020-list_field-0_0_7.md#decision-10--joint-007-cut
[spec-020-d2]: ../spec-020-list_field-0_0_7.md#decision-2--default-resolver-shape
[spec-020-d3]: ../spec-020-list_field-0_0_7.md#decision-3--get_queryset-and-async-symmetry
[spec-020-d4]: ../spec-020-list_field-0_0_7.md#decision-4--optimizer-cooperation
[spec-020-d5]: ../spec-020-list_field-0_0_7.md#decision-5--validation--error-shapes
[spec-020-d6]: ../spec-020-list_field-0_0_7.md#decision-6--metaprimary-interaction
[spec-020-d7]: ../spec-020-list_field-0_0_7.md#decision-7--scope-boundary-vs-relation-list-fields
[spec-020-d8]: ../spec-020-list_field-0_0_7.md#decision-8--out-of-scope-boundary-with-djangoconnectionfield
[spec-020-d9]: ../spec-020-list_field-0_0_7.md#decision-9--example-app-migration-posture
[spec-020]: ../spec-020-list_field-0_0_7.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
