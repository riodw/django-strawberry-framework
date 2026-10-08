# Typing 0.0.15: to-do list

basedpyright runs in `all` mode on every Python file, in two passes (3.11 and the 3.10 floor). This file tracks the
rules still switched off and the `# pyright: ignore[...]` comments still in the tree.
Each item is fixed at the root, gated (both passes 0 errors, full suite in one pass at 100% coverage), then committed.
A split suite run on a tree other sessions are editing can drop modules from every part, so it is not a coverage gate.

Progress: 18 done, 11 to do. Ignore comments: 1024 lines (1897 at the start of 0.0.15's ignore sweep).

## Pre-commit (`uvx pre-commit run --all-files`, d322f477, clean clone)

| Hook | Result | Time | Scope |
| --- | --- | --- | --- |
| kanban tracked path constants | pass | 0.2s | whole tracked set |
| source layout | pass | 4.5s | 606 files checked, 81 excluded, 0 violations |
| ruff check | pass | 0.4s | 486 files |
| ruff format | pass | 0.1s | 486 files |
| basedpyright | pass | 23.5s | 486 files, 0 errors |
| basedpyright floor (3.10) | pass | 14.8s | 486 files, 0 errors |
| public API type completeness | pass | 4.8s | 100%, 2 allowlisted warnings |
| kanban anchors | pass | 1.1s | 77 cards, 146 glossary anchors |
| citations | pass | 3.3s | 3226 citations |
| **Total** | **9/9 pass** | **55s wall** | |

## Done

- [x] 1. `reportExplicitAny` on for the package, the example project and scripts
- [x] 2. tests/ passes `all` mode in both passes; scope is every Python file
- [x] 3. Package annotations state their run-time contract
- [x] 4. Resolvers declare `graphql_type=` and return honest model rows (94 ignores)
- [x] 5. `definition_raises`, `module_binding`, direct module patching, `blocked_modules` (239 ignores)
- [x] 6. Walker hands `get_queryset` a real `strawberry.Info` on the prefetch path; bare `Info` in place of
  `Info[Any, Any]` (4 ignores)
- [x] 18. `FilterSet.__init__` overrides spell out their parameters instead of `*args, **kwargs` (10 ignores)
- [x] 25. `_CrLampKiosk` renamed `CrLampKiosk`, clearing its `reportUnusedClass` (1 ignore)
- [x] 22. The queryset-state check accepts only a tuple `_fields`, as Django stores it
- [x] 14. `utils/_queryset_private.py` reads and writes Django's private QuerySet attributes; 156 lines to 35
- [x] 15. Real `User` / `AnonymousUser` objects instead of stand-in users (39 ignores)
- [x] 16. `tests/_idioms.py::relay_hooks` / `async_relay_hooks` read the Relay methods the finalizer installs (26
  ignores; one kept, below)
- [x] 17. `tests/_info.py` builds real Strawberry `Info` objects (`make_info`, `response_path`) and `unread_info()`,
  a real `Info` that fails on any read (35 ignores: the 22 `Info` stand-ins and 13 other stand-ins)
- [x] 26. `schema_config_from_info`'s docstring names the real Strawberry `Info` as the fallback's caller; the
  `info.schema.config` fallback stays (a real `Info`'s `schema` is the Strawberry `Schema`)
- [x] 27. spec-020 and spec-023 show resolvers in the item-4 spelling (`graphql_type=`, model-row return)
- [x] 19. The field factories declare the value they resolve to: `DjangoListField(T)` is `list[T]`,
  `DjangoConnectionField(T)` is `DjangoConnection[T]`, `DjangoNodeField(T)` is `T | None`, `DjangoNodesField(T)` is
  `list[T | None]`, and `current_user()` is `object` (5 ignores)
- [x] 20. `tests/_execution.py::make_execution_context` and `tests/_definition.py::make_definition` build real
  `ExecutionContext` / `DjangoTypeDefinition` objects; hostile stand-ins keep their ignores (43 ignores, 15 of them
  other stand-ins)
- [x] 21. The other stand-ins and the uncategorized rest: real objects and models in place of stand-ins, real
  functions marked with `vars(fn).update(...)`, Django wrapper plants through `monkeypatch`, and `make_info` builds
  `operation` / `document` / `operation_name`; `Meta.description` takes a `str` or a lazy translation string; every
  kept ignore's reason line states its real cause (272 ignores)

## To do: rules still off

Counts are the diagnostics each rule reports when switched on (main pass, all seven on at once). Migrations account for
478 of them.

- [ ] 7. `reportAny`: 9861 (package 693, tests 3014, examples 5415, scripts 739)
- [ ] 8. `reportUnannotatedClassAttribute`: 8662 (package 163, tests 6579, examples 1904, scripts 16)
- [ ] 9. `reportUnusedCallResult`: 4559 (package 79, tests 2745, examples 1463, scripts 272)
- [ ] 10. `reportUnusedParameter`: 1713 (package 50, tests 1130, examples 528, scripts 5)
- [ ] 11. `reportUnknownMemberType`: 1671 (package 75, tests 892, examples 610, scripts 94)
- [ ] 12. `reportUnknownVariableType`: 1211 (package 134, tests 590, examples 426, scripts 61)
- [ ] 13. `reportUnknownArgumentType`: 660 (package 141, tests 374, examples 98, scripts 47)

Off by design (not planned): `reportImplicitStringConcatenation`, `reportPrivateUsage`, `reportUnusedFunction`,
`reportImportCycles`, `reportUninitializedInstanceVariable`. The reasons are in `pyproject.toml`.

Off at the 3.10 floor only: the five `reportUnknown*` rules and `reportUnnecessaryTypeIgnoreComment`. django-stubs needs
`typing.Self` (3.11), so at 3.10 every `-> Self` reads as unknown.

## Ignore refactors: survey verdicts

Survey verdicts recorded so nothing is re-tried blind:

- Item 14, rejected: a `stubPath` overlay of django-stubs (splits class identity, 1044 errors), a django-stubs PR for
  the private attributes (too slow), and asserting through public behavior instead (weakens the tests' claims)
- Item 16 keeps one ignore of its own: the plain-function `resolve_typename` planted before finalize in
  `tests/types/test_relay_interfaces.py` (an attribute set, not a read)
- Keep, reason lines accurate: `check_permission`'s `Any`; the `schema.py` / `consumers.py` verbatim forwards; the
  ModelForm / ModelSerializer forwards in examples; Django model `Meta` on proxy / MTI children; `connection.py`'s two
  ignores the Strawberry survey looked at
- Rejected: making `DjangoType` generic over its model (rows and GraphQL types stay unrelated classes)
- Item 21, not taken: aliasing asgiref's coroutine marker; `is_marked_coroutine_function` keeps its two suppressions
  with their real reasons (typeshed deprecates `asyncio.iscoroutinefunction` from 3.11; asgiref picks its check by
  `hasattr`)

## Waiting on you

- [ ] 23. Draft a djangorestframework-stubs issue for `ModelSerializer.Meta` (`Meta: ClassVar[type[object]]`)? It would
  retire 136 ignores once released
- [ ] 24. Type `info` as `Info` on the public visibility helpers (`apply_cascade_permissions`, `FilterSet.apply_sync`,
  ...): 23 functions and about 65 test calls; a public API change
- [ ] 28. Widen `DjangoType.get_queryset`'s return to a union? It breaks the direct sync calls in `docs/README.md` and
  fakeshop; stopped
- [ ] 29. Type the forms `files` argument (`dict[str, object]` today) as `MultiValueDict`? Values reaching it through
  the `Upload` input are not all files (the attempt met null and str), so it needs a runtime guard first; stopped

Open question from item 6: on the prefetch path the hook's `info.field_name` and `selected_fields` describe the field
whose plan reached the relation, not the nested relation. Keep (as documented), or build a per-field raw info as
strawberry_django does?

## Ignore breakdown

Lines carrying `# pyright: ignore[...]`: 1024 (1053 rule hits) in 164 files: tests 794, package 175, examples 53,
scripts 2.

### By cause

| Cause | Lines | Plan |
| --- | --- | --- |
| Deliberately ill-typed test input (hostile values, forged classes, rejected writes) | 490 | keep |
| Django private QuerySet attributes (seam 14, `super()._clone()` 2, hostile writes 7, planted shapes 12) | 35 | keep |
| DRF stubs declare `ModelSerializer.Meta` | 136 | item 23 |
| Verbatim `__init__` forwards (schema, consumers, ModelForm, ModelSerializer) | 34 | keep |
| Framework `Meta` read from the class body only | 13 | keep |
| Django model `Meta` on proxy / MTI children | 11 | keep |
| Reviewed in item 21 and kept (each reason line states its cause) | 301 | keep |
| Mixin bases whose `__init__` chain reaches one base (enum filter fields, `PaginationArgumentError`) | 4 | keep |

### By rule

| Rule | Hits | Package | Tests | Examples | Scripts |
| --- | --- | --- | --- | --- | --- |
| `reportArgumentType` | 320 | 24 | 291 | 5 | 0 |
| `reportIncompatibleVariableOverride` | 194 | 2 | 169 | 23 | 0 |
| `reportAttributeAccessIssue` | 186 | 25 | 160 | 1 | 0 |
| `reportExplicitAny` | 101 | 67 | 19 | 13 | 2 |
| `reportIncompatibleMethodOverride` | 69 | 5 | 59 | 5 | 0 |
| `reportReturnType` | 26 | 0 | 25 | 1 | 0 |
| `reportUnnecessaryIsInstance` | 20 | 20 | 0 | 0 | 0 |
| `reportCallIssue` | 17 | 1 | 15 | 1 | 0 |
| `reportUnsafeMultipleInheritance` | 13 | 8 | 3 | 2 | 0 |
| `reportAssignmentType` | 12 | 0 | 11 | 1 | 0 |
| `reportIndexIssue` | 11 | 0 | 11 | 0 | 0 |
| `reportUnknownParameterType` | 9 | 1 | 8 | 0 | 0 |
| `reportMissingSuperCall` | 8 | 2 | 6 | 0 | 0 |
| `reportUnreachable` | 7 | 5 | 2 | 0 | 0 |
| `reportGeneralTypeIssues` | 7 | 1 | 6 | 0 | 0 |
| `reportUndefinedVariable` | 7 | 0 | 7 | 0 | 0 |
| `reportFunctionMemberAccess` | 6 | 4 | 1 | 1 | 0 |
| `reportMissingParameterType` | 5 | 0 | 5 | 0 | 0 |
| `reportPropertyTypeMismatch` | 4 | 4 | 0 | 0 | 0 |
| `reportUnnecessaryComparison` | 4 | 4 | 0 | 0 | 0 |
| `reportDeprecated` | 4 | 3 | 1 | 0 | 0 |
| `reportInvalidTypeArguments` | 3 | 1 | 2 | 0 | 0 |
| `reportOptionalMemberAccess` | 3 | 3 | 0 | 0 | 0 |
| `reportInvalidCast` | 3 | 3 | 0 | 0 | 0 |
| `reportIncompatibleUnannotatedOverride` | 3 | 1 | 2 | 0 | 0 |
| `reportInvalidTypeForm` | 3 | 0 | 3 | 0 | 0 |
| `reportUntypedFunctionDecorator` | 2 | 2 | 0 | 0 | 0 |
| `reportUntypedBaseClass` | 2 | 0 | 2 | 0 | 0 |
| `reportImplicitOverride` | 1 | 0 | 1 | 0 | 0 |
| `reportUnusedImport` | 1 | 0 | 1 | 0 | 0 |
| `reportUnknownLambdaType` | 1 | 0 | 1 | 0 | 0 |
| `reportMissingTypeArgument` | 1 | 0 | 1 | 0 | 0 |

### Most ignores per file

| File | Lines |
| --- | --- |
| `tests/utils/test_querysets.py` | 71 |
| `tests/rest_framework/test_resolvers.py` | 66 |
| `tests/rest_framework/test_sets.py` | 48 |
| `tests/rest_framework/test_converter.py` | 42 |
| `tests/test_resource_policy.py` | 29 |
| `examples/fakeshop/apps/library/serializers.py` | 26 |
| `tests/test_list_field.py` | 22 |
| `tests/test_consumers.py` | 20 |
| `tests/utils/test_relations.py` | 18 |
| `tests/test_error_policy.py` | 17 |

## Addendum: items 11-13 root-fix analysis (2026-10-08, HEAD 85ba203e)

Items 11-13 (`reportUnknownMemberType`, `reportUnknownVariableType`, `reportUnknownArgumentType`) were analyzed together
because they share causes: most fixes clear rows in two or three of the rules at once. Method: one Sonnet gatherer per
rule grouped every diagnostic by origin, then one Opus analyst per rule verified the groups and prototyped fixes in a
`git archive` scratch copy (13 basedpyright runs, no pytest). Nothing is implemented; the repo is unchanged. The
scratch reports and run outputs lived under `/private/tmp` and will not survive a reboot, so everything needed to resume
is below.

### Baseline (only these three rules on, main pass, 85ba203e)

| Rule | Total | Package | Tests | Examples | Scripts | Other |
| --- | --- | --- | --- | --- | --- | --- |
| `reportUnknownMemberType` (11) | 1517 | 72 | 720 | 631 | 93 | 1 |
| `reportUnknownVariableType` (12) | 1176 | 134 | 556 | 425 | 57 | 4 |
| `reportUnknownArgumentType` (13) | 664 | 136 | 378 | 102 | 45 | 3 |

These differ from the to-do list counts above, which were taken with all seven rules on at an earlier HEAD; re-baseline
those lines when an item lands. "Other" is root files (`conftest.py`, `line_count.py`, `docs/dry/export_dry_review.py`).

To measure: `git archive HEAD` into a scratch dir, set the three rules to `"error"` in its `pyproject.toml`, and give the
`examples/fakeshop` executionEnvironment `extraPaths = ["."]` (without it the copy checks examples against the real
installed package). One whole-tree run takes about 15 s.

### Causes, largest first

| Cause | Member | Variable | Argument | Package rows | Fix |
| --- | --- | --- | --- | --- | --- |
| django-stubs `Field[_ST, _GT]` has no TypeVar defaults and binds neither in `__init__`; the mypy plugin fills them, basedpyright never does. Every field declaration and every attribute read through `Field.__get__` is Unknown; also M2M `_To`, forms `_M`, `QuerySet.__init__` not binding `_Model` | 681 | 550 | 99 | 3 | decision 1 |
| Empty `[]` / `{}` / `set()` / `getattr(...) or {}` with no declared element type, and names derived from them | 448 | 185 | 217 | 19 | declare the type where the literal is born |
| `isinstance` / `type(x) is C` on an `object` / `Any` value narrows to `C[Unknown]` in invariant slots (`dict`, `list`, `set`, `Mapping` key, `tuple`, `GraphQLList`); `strictGenericNarrowing` (already on in `all` mode) only covers covariant slots | 38 | 124 | 149 | 182 | narrowing predicates |
| Deliberate unbound builtin slot calls (`dict.items(v)`, `list.__iter__(v)`, `Mapping.get(m, k)`) specialize the bare class with Unknown | 28 | 19 | 13 | 43 | spelled specialization |
| djangorestframework-stubs bare generics: `BindingDict` / `get_fields` / `_declared_fields` over bare `Field`, `child_relation`, `errors -> ReturnDict`, validator `queryset`, `RelatedField.__new__` cannot bind `_MT` | 54 | 146 | 100 | about 30 | accessors + upstream PR (item 23) |
| Bare `type` annotations on test helpers (`make_django_type -> type`) | 85 | 34 | 40 | 0 | `type[DjangoType]`, generic over the model |
| Strawberry `schema/_graphql_core.py` imports graphql-core 3.3 names in a `try` and rebinds the `TypeAlias` names in the `except`, so under our `<3.3` pin `StreamResult` / `ExecutionContext.result` carry Unknown | 22 | 39 | 9 | about 10 | boundary + upstream issue |
| Expressions on lines whose error is already suppressed evaluate to Unknown (private QuerySet attributes, `super()._clone()`, uuid slot, router) | about 50 | 44 | 18 | about 25 | add the rule to the existing bracket, or stop the Unknown on that line |
| `consumers.py` subclasses deliberate `Any` bases, so `super().x` is Unknown | 13 | 1 | 3 | 14 | checker-only shape classes |
| Generated `kanban/constants.py` tuple has 351 entries; inference caps at 256 | 1 | 9 | 5 | 0 | generator emits `tuple[str, ...]` |
| Small: graphql-core 3.2 bare `GraphQLWrappingType`, Strawberry bare `StrawberryResolver` / `staticmethod`, debug-toolbar `Panel.title`, django-filter stubs, return-only TypeVars, `request_from_info -> object` | rest | rest | rest | about 20 | see below |

### Fixes, with prototype evidence

1. **Narrowing predicates.** One private module (for example `utils/_narrowing.py`) of predicates that run exactly the
   check each site uses: `is_dict`, `is_list`, `is_tuple`, `is_set`, `is_frozenset`, `is_list_or_tuple`, `is_mapping ->
   Mapping[object, object]`, `is_class -> type[object]`, `is_memoryview`, `is_graphql_list`. Exact-type checks (`type(x)
   is dict`) use `TypeGuard`, not `TypeIs`. Class-specific predicates stay local to their module (DRF `Field`,
   `ModelChoiceField`, exact `QuerySet`). It absorbs the existing private copies (`utils/querysets.py`'s `_is_exact_*`,
   two `_is_class`) and retires about 20 of the package's 27 `cast("<container>[object...]")` calls plus a
   `reportUnnecessaryIsInstance` ignore in `utils/policies.py`. `TypeIs` is fine despite the `typing-extensions>=4.4.0`
   floor: the package already imports it only under `TYPE_CHECKING` (`relay.py`, `_graphql_core_patches.py`). A name
   must be guarded at every narrowing in its function, or the unguarded branch keeps the row. Predicates only suit
   `object` / `Any` subjects; on a typed union the positive branch drops the specific arm.
2. **Typed unbound slots.** `tuple(dict[object, object].items(value))`, `Mapping[str, object].get(self._scope, key)`.
   Runtime-identical (`dict[object, object].items is dict.items` holds on 3.10, 3.11, 3.14) and keeps the subclass-override
   bypass. The argument analyst's zero-cost variant declares `dict_items_slot` etc. under `TYPE_CHECKING` and binds
   `dict.items` at runtime. Pair with the predicates: the argument must already be the specialized type.
3. **Prototype result for 1 + 2:** package Argument 136 -> 13, package Variable down 61-88, package Member own-code rows
   32 of 33 cleared. Files: `utils/canonical.py`, `utils/input_values.py`, `utils/inputs.py`, `utils/permissions.py`,
   `utils/context.py`, `conf.py`, `filters/sets.py`, `utils/relations.py`, `optimizer/extension.py`, about 30 package
   files in total.
4. **Latent defects the Unknowns were hiding** (each needs its own root fix and test, not a suppression):
   `types/base.py` (the `Meta.connection`, `Meta.relation_shapes`, `Meta.optimizer_hints` returns), `filters/sets.py`
   (`data.update(normalized)` and the operator-bag `list(raw_value.items())`), `rest_framework/resolvers.py` (nested
   `child_data` keys, NESTED_MULTI `items` iterated from an `object`, and `_assert_intent_specs` iterating an `object`),
   `utils/inputs.py` (`raw_kwargs`), `utils/policies.py::resolve_policy` (override names), `connection.py` (`list[object]`
   window rows passed to `rows: list[Model]`). The pattern: a dict validated key by key with `isinstance(key, str)` is
   returned as `dict[str, ...]`; build the typed value inside the validating loop (verified on `relation_shapes`). The
   `utils/inputs.py` and `utils/policies.py` sites are on hostile-input paths.
5. **Own-API Unknowns:** type `rest_framework/resolvers.py::_RelationLedger.consume` (now `-> Any`) as the snapshot or a
   typed sentinel; `mutations/resolvers.py::_run_mutation_steps` tells failure from success by `isinstance(x, list)`,
   which is also a real ambiguity for a decode step that returns a list, so use a tagged failure wrapper.
6. **Empty containers:** declare at the defining statement with the real element type (`object` pushes narrowing work
   downstream; annotating a test's `self.consumers: list[object] = []` produced 17 new errors where elements are read
   back). For `getattr(...) or {}`: `extensions: Mapping[str, object] = getattr(field_def, "extensions", None) or {}`.
   `forms/resolvers.py`: hoist the inline empty-values default to `_EMPTY_VALUES: tuple[object, ...]` (django-stubs types
   `EMPTY_VALUES: Any`). 207 declarations in about 45 files; package rows all cleared in the prototype.
7. **DRF accessors:** `bound_fields(serializer) -> Mapping[str, DRFField]` needs no suppression because `BindingDict` is
   not generic (took `tests/rest_framework/test_converter.py` Argument 60 -> 14, Variable 71 -> 25). A Protocol-typed
   parameter also works but must declare `fields` with `@cached_property`; a plain `@property` fails assignability.
   `child_relation_of`, `serializer_errors` and `_declared_fields` reads need one suppression line each (a partially
   Unknown `return` is always a Variable-rule site, even under a declared return type).
8. **Consumers:** checker-only shape classes in the existing `if TYPE_CHECKING:` block of `consumers.py`
   (`_HandlerBase`, `_TransportWSHandlerBase`, `_GraphQLWSHandlerBase`, `_WebSocketAdapterBase`, `_ConsumerBase`), each
   base bound as `type[_Shape] = getattr(...)`. Cleared 12/12 rows and retired 4 `reportExplicitAny` ignores. Leaves 2
   `reportAssignmentType` where the consumer installs its handler classes (1 suppression each) and 1 `reportReturnType`
   (deriving `_ConsumerBase` from `RevalidatingGraphQLWSConsumer` should settle it; not run). `type[Protocol]` bases
   fail (`reportAbstractUsage`), as do shapes inheriting the existing protocols (`reportImplicitAbstractClass`).
9. **Small fixes:** `scripts/build_kanban_tracked_path_constants.py` emits `TRACKED_FILE_PATHS: tuple[str, ...] = (`
   and the same for the directory tuple (fix the generator, never the generated file; clears 9 Variable, 5 Argument and
   the `kanban/services.py::sync_tracked_paths_from_constants` `dict.fromkeys` Member row). `filters/inputs.py` and
   `orders/inputs.py` bind the `make_set_input_namespace(...)` result to a declared tuple alias before unpacking.
   `list_field.py::_is_deterministic_order_term` takes `term: object` and narrows with `type(term) is models.F`. Declare
   `parent: object = getattr(...)` where `type(<Any>)` gave `type[Unknown]`. Split `models.QuerySet(model=m).filter(...)`
   into a declared local first; `optimizer/walker.py::_hint_prefetch_over_pk_set` still reports with a declared target
   (unproven cause, probably the `cast` argument).
10. **Boundaries that cannot be fixed in this repo** (one line each, reason names the upstream defect; about 12-15
    package lines total): `DjangoSchema._stream` and `consumers.py::_StopAwareSchema.stream` (Strawberry
    `StreamResult`), `utils/typing.py::unwrap_non_null` and the other graphql-core 3.2 bare wrapping-type reads (typed
    accessors `graphql_type_of` / `return_type_of`), the `inspect_django_type.py` `from_type` calls (one local helper;
    calling `from_object` would bypass a consumer `NameConverter` override), debug-toolbar `Panel.title`, the
    `Prefetch.__new__` call (not subscriptable at runtime without django-stubs-ext), the `routers.py` `URLRouter`
    line, and extending the existing `_queryset_private.py` / `nested_fetch.py` / uuid brackets with the Unknown rules.
    `utils/permissions.py::request_from_info` returning `object` is the stopped "request_from_info passthrough" item
    (8 Member rows plus 4 ignores go with it).

### Enabling the rules for the package first

An executionEnvironment rooted at `django_strawberry_framework/` does not work: its `rest_framework/` and `types/`
subpackages shadow DRF and the stdlib (measured: `"serializers" is unknown import symbol`, +110 errors). Two working
options, both measured:

- **A. Scoped config:** `pyrightconfig.unknown.json` that `extends` `pyproject.toml`, sets `include =
  ["django_strawberry_framework"]` and the three rules to `"error"`; a third basedpyright hook in pre-commit and CI
  (about 4 s); widen `include` area by area, then fold into `pyproject.toml` and delete the file. No per-file comments.
- **B. Root config + opt-outs:** rules `"error"` at top level, `"none"` on the `scripts` and `examples/fakeshop`
  environments, and a first-line `# pyright: reportUnknown...=false` in every test file with sites (all three rules: 84
  test files + `conftest.py`, `line_count.py`, `docs/dry/export_dry_review.py`; Member alone: 69, or 61 after the
  model annotations). A comment on a file with no sites is silent. Delete each comment as its file is fixed.

The floor config keeps the Unknown rules off either way (django-stubs `-> Self` at 3.10).

### Decisions for the maintainer

1. **Django field Unknowns (about 680 Member, 550 Variable, 100 Argument rows, none in the package).**
   - Declare the solved generic on each model field: `name: models.TextField[str, str] = models.TextField(...)`,
     `category: models.ForeignKey[Category, Category] = ...`, nullable `models.DateTimeField[datetime | None, datetime |
     None]`, `models.ManyToManyField[Label]`; skip `FileField` / `ImageField` (not generic). About 315 declarations in 5
     example `models.py` files and test fixture models (`tests/_relation_fixtures.py`, `tests/optimizer/_link_models.py`,
     about 7 more test modules). Each file needs `from __future__ import annotations` (Django `Field` has no
     `__class_getitem__`; 3.10 evaluates annotations). Measured: examples Member 631 -> 46, Variable 425 -> 63, Argument
     102 -> 47. Surfaces real errors to fix: 12 `reportOptionalMemberAccess` on nullable FK reads (kanban, a library
     test, two live kanban tests), `TargetVersion` missing its `milestone_id` key-column declaration,
     `kanban/services.py` assigning an `object` parameter to `verified_at` / `ended_at`, 2 `JSONField` writes in
     `tests/mutations/test_write_transaction.py`, 1 hostile write needing the usual suppression, and 1 now-unnecessary
     `reportUnknownLambdaType` ignore in `tests/utils/test_querysets.py`. Open sub-questions: `_ST` as the read type or
     django-stubs' write type `str | Combinable`; whether to gate annotations against field kwargs (`null=True` <-> `|
     None`, FK target) since nothing else checks them without the mypy plugin.
   - Or wait for django-stubs to ship PEP 696 TypeVar defaults (a full-copy `stubPath` overlay with defaults cleared
     every row of these groups with 0 new Variable rows; neither django-stubs nor DRF-stubs master has them as of
     2026-10-08) and keep examples/tests out of scope until then. An in-repo overlay is rejected (item 14 verdict:
     splits class identity; and `default=Any` turns the rows into item 7 `Any` debt). With defaults, 7 bare-class
     `models.QuerySet.filter(<subclass>)` test sites become errors; re-spell them `QuerySet[Book].filter(...)` in the
     same change as the stub bump.
2. **Package-first mechanism:** A (scoped config, third basedpyright hook) or B (per-file opt-out comments).
3. **Predicate call cost:** one Python call per container check on input walks (`utils/input_values.py`, the
   resource-policy walk, `optimizer/extension.py::_freeze_variable_value`, the DRF freeze walk), subject to the BUILD.md
   hot-path budget; or the zero-frame variant (declare under `TYPE_CHECKING`, bind `dict.__instancecheck__` at runtime;
   single classes only).
4. **DRF:** package accessors now (recommended by all three analysts), then the upstream PR with item 23.
5. **`as_view` return types:** `views.py::_RequestBodyBoundaryMixin.as_view -> Any` matches all four
   `django.urls.path` overloads, so every `path(..., View.as_view())` is Unknown. Per-class precise returns fix it and
   help consumer URLconfs, but change the public type surface; the async view keeps one
   `reportIncompatibleMethodOverride` (django-stubs' `View.as_view` is sync-only).
6. **P04 tagged failure type** for mutation steps, and approval to fix the 10 latent defects one by one.
7. **Upstream filings:** django-stubs (TypeVar defaults on fields, M2M, forms, `QuerySet.__init__(model: type[_Model])`;
   reviewers may prefer django-types-style `null: Literal[True]` overloads since a default cannot see `null=True`),
   djangorestframework-stubs (with item 23), Strawberry (`_graphql_core.py` alias rebinding; confirm on graphql-core 3.3
   first), django-debug-toolbar (`Panel.title`), typeshed django-filter stubs, typeshed channels stubs (the `login` /
   `logout` scope arguments in `auth/mutations.py`).

### Recommended order when this is picked up

1. Package own code: predicates + typed slots, then the latent defects each with its own test, then P03/P04, empty
   containers, consumers shapes, the small fixes. Shared across all three rules.
2. Package third-party boundaries and bracket extensions; package at 0 unsuppressed rows for all three rules.
3. Land the enablement mechanism (decision 2) for the package.
4. Generator fix, then examples (decision 1), scripts (containers + one `TypedDict` per JSON payload in
   `prove_failability.py`), tests (containers, `type[DjangoType]` helpers, `bound_fields`), dropping overrides or
   comments as each area reaches 0.
5. Then item 7 (`reportAny`): several fixes here move rows from Unknown to `Any`, so do not start 7 first.

### Notes for the next agent

- Read AGENTS.md and START.md first. No pytest unless the maintainer asks (AGENTS rule 15), including in agent briefs
  and scratch copies. One heavy job machine-wide: check `pgrep -fl '[p]ytest|[b]asedpyright'` and serialize
  basedpyright runs; two concurrent suites plus checker pairs OOM-crashed this 16 GB Mac on 2026-10-08 and the reboot
  wiped `/private/tmp`.
- Every commit for these items includes this file, updated in that commit; re-baseline the item lines with the
  measurement above.
- Prototype in a `git archive` scratch copy with the examples `extraPaths` fix, never by running fakeshop scripts or
  `manage.py` (they write the tracked `examples/fakeshop/db.sqlite3`).
- Subagents cannot write report files (the harness refuses); have them return the report as text and save it yourself.
- Done lines name the item and its ignore count, never a commit hash; one commit per item, never a follow-up hash
  commit. This is a temp file, deleted once the rules are on and the ignores are gone.
- Attributions above were verified with checker runs except where marked unproven (`_hint_prefetch_over_pk_set`,
  `_ConsumerBase` return type, T02 / S11 test annotations).


<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
