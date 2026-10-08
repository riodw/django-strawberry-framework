# Typing 0.0.15: to-do list

basedpyright runs in `all` mode on every Python file, in two passes (3.11 and the 3.10 floor). This file tracks the
rules still switched off and the `# pyright: ignore[...]` comments still in the tree.
Each item is fixed at the root, gated (both passes 0 errors, full suite in one pass at 100% coverage), then committed.
A split suite run on a tree other sessions are editing can drop modules from every part, so it is not a coverage gate.

Progress: 18 done, 9 to do. Ignore comments: 1024 lines (1897 at the start of 0.0.15's ignore sweep).

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
