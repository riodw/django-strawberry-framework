# Typing 0.0.15: to-do list

basedpyright runs in `all` mode on every Python file, in two passes (3.11 and the 3.10 floor). This file tracks the
rules still switched off and the `# pyright: ignore[...]` comments still in the tree.
Each item is fixed at the root, gated (both passes 0 errors, full suite in one pass at 100% coverage), then committed.
A split suite run on a tree other sessions are editing can drop modules from every part, so it is not a coverage gate.

Progress: 22 done, 7 to do. Ignore comments: 1137 lines (1897 at the start of 0.0.15's ignore sweep).

## Pre-commit (`uvx pre-commit run --all-files`, 4ce779e1, clean clone)

| Hook | Result | Time | Scope |
| --- | --- | --- | --- |
| kanban tracked path constants | pass | 0.1s | whole tracked set |
| source layout | pass | 3.4s | 633 files checked, 81 excluded, 0 violations |
| ruff check | pass | 0.4s | 511 files |
| ruff format | pass | 0.1s | 511 files |
| basedpyright | pass | 16.4s | 511 files, 0 errors |
| basedpyright floor (3.10) | pass | 14.6s | 511 files, 0 errors |
| public API type completeness | pass | 4.8s | 100%, 2 allowlisted warnings |
| kanban anchors | pass | 1.1s | 77 cards, 149 glossary anchors |
| citations | pass | 3.4s | 3400 citations |
| **Total** | **9/9 pass** | **45s wall** | |

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
- [x] 14. `utils/_queryset_private.py` reads and writes Django's private QuerySet attributes; 156 ignore lines to 35
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
- [x] 11. `reportUnknownMemberType` on everywhere: every Django model field annotated with the generic the django-stubs
  plugin would solve, gated against the field call by `tests/test_model_field_annotations.py`; typed DRF reads in
  `rest_framework/accessors.py`
- [x] 12. `reportUnknownVariableType` on everywhere: containers declared with their element type where they are born,
  and the narrowing predicates in `utils/_narrowing.py` in place of `isinstance` on `object` values; write-pipeline
  steps fail through a tagged `StepFailure` instead of a bare list
- [x] 13. `reportUnknownArgumentType` on everywhere: typed unbound slots (`dict_items`, `mapping_get`), per-view
  `as_view` returns, and checker-only shape classes for the bases the consumer factory reads at run time; 76
  suppression lines carry one of the three rules, each naming the third-party defect
- [x] 10. `reportUnusedParameter` on everywhere: a parameter the caller passes by position is renamed `_name`, a
  fixture requested for its side effect moves to `@pytest.mark.usefixtures`, an optional Strawberry `root` / `info`
  or unread private parameter is removed, and `NestedConnectionStrategy.plan` takes its arguments positional-only;
  98 suppression lines keep a parameter a caller binds by name

## To do: rules still off

Counts are the diagnostics each rule reports when switched on (main pass, all four on at once, measured once items
11-13 were on). "Root" is `conftest.py`, `line_count.py` and `docs/dry/export_dry_review.py`. Migrations account for 455
of them.

- [ ] 7. `reportAny`: 9636 (package 637, tests 2932, examples 5338, scripts 634, root 95). The kanban scripts' GraphQL
  boundary stays here: `scripts/_kanban_lib.py::fetch_graphql_data` returns `dict[str, Any]`, and the `TypedDict`
  payloads it feeds (`IdRow`, `LabelRef`, ...) are only as true as that `Any`; retyping it to `object` needs a runtime
  validator that narrows the payload into those `TypedDict`s, keeping today's behavior on a malformed response
- [ ] 8. `reportUnannotatedClassAttribute`: 8365 (package 0, tests 6684, examples 1681, scripts 0, root 0); on for
  scripts/, the package and the root files (their execution environments in `pyproject.toml`)
- [ ] 9. `reportUnusedCallResult`: 4425 (package 0, tests 2897, examples 1527, scripts 0, root 0); on for scripts/, the
  package and the root files

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
  retire 142 ignores once released
- [ ] 24. Type `info` as `Info` on the public visibility helpers (`apply_cascade_permissions`, `FilterSet.apply_sync`,
  ...): 23 functions and about 65 test calls; a public API change
- [ ] 28. Widen `DjangoType.get_queryset`'s return to a union? It breaks the direct sync calls in `docs/README.md` and
  fakeshop; stopped
- [ ] 29. Type the forms `files` argument (`dict[str, object]` today) as `MultiValueDict`? Values reaching it through
  the `Upload` input are not all files (the attempt met null and str), so it needs a runtime guard first; stopped
- [ ] 30. File the upstream issues behind the Unknown-rule suppressions? Each would retire suppression lines once
  released: django-stubs (PEP 696 TypeVar defaults on `Field`, the M2M `_To`, forms; `QuerySet.__init__` binding
  `_Model`; a generic `Prefetch`; the private attributes it omits; a `re_path` overload taking an ASGI application;
  reviewers may prefer django-types-style `null: Literal[True]` overloads, since a default cannot see `null=True`),
  djangorestframework-stubs (with item 23: `get_fields()` / `_declared_fields` / `BindingDict` over bare `Field`,
  `child_relation`, `ListField.child`, `errors -> ReturnDict`, the validators' `queryset`, `RelatedField.__new__`
  unable to bind its model), Strawberry (`schema/_graphql_core.py` rebinding its graphql-core 3.3 result aliases in an
  `ImportError` fallback, confirm on graphql-core 3.3 first; bare `StrawberryResolver`, `StrawberryDirective`,
  `staticmethod`, `asyncio.Task`), graphql-core 3.2 (bare `GraphQLWrappingType` / `GraphQLList`), django-debug-toolbar
  (`Panel.title`, `show_toolbar_func_or_path`'s bare `Callable`), typeshed django-filter (`Filter.method` is a
  property), typeshed channels (the closed `_ChannelScope` scope `TypedDict`; the `login` / `logout` scope arguments in
  `auth/mutations.py`), pytest (`MonkeyPatch.syspath_prepend`'s `path`) and asgiref (the communicator's unannotated
  parameters and returns)

Open question from item 6: on the prefetch path the hook's `info.field_name` and `selected_fields` describe the field
whose plan reached the relation, not the nested relation. Keep (as documented), or build a per-field raw info as
strawberry_django does?

## Ignore breakdown

Lines carrying `# pyright: ignore[...]`: 1137 (1233 rule hits) in 193 files: tests 846, package 203, examples 85,
scripts 2, root 1.

### By cause

Classified by each line's reason comment. "Unknown too" counts the lines whose bracket also names one of the three
Unknown rules because the expression already suppressed for another rule evaluates to Unknown.

| Cause | Lines | Unknown too | Plan |
| --- | --- | --- | --- |
| Deliberately ill-typed test input (hostile values, forged classes, stand-ins, rejected writes) | 426 | 4 | keep |
| DRF stubs declare `ModelSerializer.Meta` | 148 | 0 | item 23 |
| Django private QuerySet attributes (seam, `super()._clone()`, hostile writes, planted shapes) | 17 | 8 | keep |
| Verbatim forwards (schema, consumers, ModelForm, ModelSerializer, field and `strawberry.type` forwards) | 42 | 0 | keep |
| Django model `Meta` on proxy / MTI children | 10 | 0 | keep |
| Third-party annotations only the Unknown rules report: Strawberry 16 (11 the `_graphql_core.py` alias rebinding, 5 bare generics), django-stubs 9 (7 migration M2M `_To`, `Prefetch`, a `re_path` route list), drf-stubs 8, graphql-core 3.2 bare generics 3, django-debug-toolbar 3, pytest 3, asgiref 1 | 43 | 43 | item 30 |
| Parameters a caller binds by name that the body never reads (keyword-called hooks and callbacks, Strawberry argument probes, upstream-verbatim signatures, fixtures a fixture requests for setup or teardown order, parametrize columns); three more share lines counted elsewhere | 95 | 0 | keep |
| The rest, reviewed in item 21 or added since, each reason line stating its cause (framework `Meta` reads, mixin `__init__` chains, filter overrides, `Any` forwards, django-stubs / typeshed omissions) | 356 | 21 | keep |

### By rule

| Rule | Hits | Package | Tests | Examples | Scripts | Root |
| --- | --- | --- | --- | --- | --- | --- |
| `reportArgumentType` | 316 | 24 | 287 | 5 | 0 | 0 |
| `reportIncompatibleVariableOverride` | 210 | 5 | 178 | 27 | 0 | 0 |
| `reportAttributeAccessIssue` | 153 | 26 | 126 | 1 | 0 | 0 |
| `reportExplicitAny` | 100 | 62 | 22 | 14 | 2 | 0 |
| `reportUnusedParameter` | 98 | 7 | 72 | 18 | 0 | 1 |
| `reportIncompatibleMethodOverride` | 74 | 7 | 62 | 5 | 0 | 0 |
| `reportUnknownMemberType` | 60 | 29 | 29 | 2 | 0 | 0 |
| `reportUnknownVariableType` | 38 | 23 | 15 | 0 | 0 | 0 |
| `reportReturnType` | 27 | 1 | 25 | 1 | 0 | 0 |
| `reportUnnecessaryIsInstance` | 19 | 19 | 0 | 0 | 0 | 0 |
| `reportCallIssue` | 15 | 1 | 13 | 1 | 0 | 0 |
| `reportAssignmentType` | 14 | 0 | 13 | 1 | 0 | 0 |
| `reportUnknownArgumentType` | 14 | 4 | 3 | 7 | 0 | 0 |
| `reportUnsafeMultipleInheritance` | 13 | 8 | 3 | 2 | 0 | 0 |
| `reportIndexIssue` | 10 | 0 | 10 | 0 | 0 | 0 |
| `reportMissingSuperCall` | 7 | 2 | 5 | 0 | 0 | 0 |
| `reportUndefinedVariable` | 7 | 0 | 7 | 0 | 0 | 0 |
| `reportUnreachable` | 7 | 5 | 2 | 0 | 0 | 0 |
| `reportFunctionMemberAccess` | 6 | 4 | 1 | 1 | 0 | 0 |
| `reportUnnecessaryComparison` | 6 | 5 | 1 | 0 | 0 | 0 |
| `reportGeneralTypeIssues` | 5 | 0 | 5 | 0 | 0 | 0 |
| `reportPropertyTypeMismatch` | 5 | 5 | 0 | 0 | 0 | 0 |
| `reportDeprecated` | 4 | 3 | 1 | 0 | 0 | 0 |
| `reportUnknownParameterType` | 4 | 1 | 3 | 0 | 0 | 0 |
| `reportIncompatibleUnannotatedOverride` | 3 | 1 | 2 | 0 | 0 | 0 |
| `reportInvalidCast` | 3 | 3 | 0 | 0 | 0 | 0 |
| `reportInvalidTypeArguments` | 3 | 1 | 2 | 0 | 0 | 0 |
| `reportInvalidTypeForm` | 3 | 0 | 3 | 0 | 0 | 0 |
| `reportOptionalMemberAccess` | 3 | 3 | 0 | 0 | 0 | 0 |
| `reportUntypedFunctionDecorator` | 2 | 2 | 0 | 0 | 0 | 0 |
| `reportImplicitOverride` | 1 | 0 | 1 | 0 | 0 | 0 |
| `reportMissingTypeArgument` | 1 | 0 | 1 | 0 | 0 | 0 |
| `reportUntypedBaseClass` | 1 | 0 | 1 | 0 | 0 | 0 |
| `reportUnusedImport` | 1 | 0 | 1 | 0 | 0 | 0 |

### Most ignores per file

| File | Lines |
| --- | --- |
| `tests/rest_framework/test_resolvers.py` | 72 |
| `tests/utils/test_querysets.py` | 66 |
| `tests/rest_framework/test_sets.py` | 50 |
| `tests/rest_framework/test_converter.py` | 45 |
| `tests/test_resource_policy.py` | 32 |
| `examples/fakeshop/apps/library/serializers.py` | 30 |
| `tests/types/test_relay_interfaces.py` | 24 |
| `tests/test_list_field.py` | 22 |
| `tests/rest_framework/test_inputs.py` | 20 |
| `tests/test_error_policy.py` | 18 |


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
