# Typing 0.0.15: to-do list

basedpyright runs in `all` mode on every Python file, in two passes (3.11 and the 3.10 floor). This file tracks the
rules still switched off and the `# pyright: ignore[...]` comments still in the tree.
Each item is fixed at the root, gated (both passes 0 errors, full suite in one pass at 100% coverage), then committed.
A split suite run on a tree other sessions are editing can drop modules from every part, so it is not a coverage gate.

Progress: 15 done, 12 to do. Ignore comments: 1339 lines (1897 at the start of 0.0.15's ignore sweep).

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

## To do: ignore refactors (from the 2026-10-06 survey)

- [ ] 19. Precise return types on `DjangoListField` / `DjangoConnectionField` / `DjangoNodeField` /
  `DjangoNodesField`: 4. Run the public-types check first
- [ ] 20. Real `ExecutionContext` / `DjangoTypeDefinition` objects instead of stand-ins: 36, case by case
- [ ] 21. Not yet surveyed: other stand-ins (168) and the uncategorized rest (420, of which 153 are in the package)

Survey verdicts recorded so nothing is re-tried blind:

- Item 14, rejected: a `stubPath` overlay of django-stubs (splits class identity, 1044 errors), a django-stubs PR for
  the private attributes (too slow), and asserting through public behavior instead (weakens the tests' claims)
- Item 16 keeps one ignore of its own: the plain-function `resolve_typename` planted before finalize in
  `tests/types/test_relay_interfaces.py` (an attribute set, not a read)
- Keep, reason lines accurate: `check_permission`'s `Any`; the `schema.py` / `consumers.py` verbatim forwards; the
  ModelForm / ModelSerializer forwards in examples; Django model `Meta` on proxy / MTI children; `connection.py`'s two
  ignores the Strawberry survey looked at
- Rejected: making `DjangoType` generic over its model (rows and GraphQL types stay unrelated classes)

## Waiting on you

- [ ] 23. Draft a djangorestframework-stubs issue for `ModelSerializer.Meta` (`Meta: ClassVar[type[object]]`)? It would
  retire 136 ignores once released
- [ ] 24. Type `info` as `Info` on the public visibility helpers (`apply_cascade_permissions`, `FilterSet.apply_sync`,
  ...): 23 functions and about 65 test calls; a public API change

Open question from item 6: on the prefetch path the hook's `info.field_name` and `selected_fields` describe the field
whose plan reached the relation, not the nested relation. Keep (as documented), or build a per-field raw info as
strawberry_django does?

## Ignore breakdown

Lines carrying `# pyright: ignore[...]`: 1339 (1368 rule hits) in 175 files: tests 1097, package 184, examples 56,
scripts 2.

### By cause

| Cause | Lines | Plan |
| --- | --- | --- |
| Deliberately ill-typed test input (hostile values, forged classes, rejected writes) | 482 | keep |
| Other stand-in objects in tests | 168 | item 21 |
| Django private QuerySet attributes (seam 14, `super()._clone()` 2, hostile writes 7, planted shapes 12) | 35 | keep |
| DRF stubs declare `ModelSerializer.Meta` | 136 | item 23 |
| Stand-in execution contexts / definitions | 36 | item 20 |
| Verbatim `__init__` forwards (schema, consumers, ModelForm, ModelSerializer) | 34 | keep |
| Framework `Meta` read from the class body only | 13 | item 21 |
| Django model `Meta` on proxy / MTI children | 11 | keep |
| Field factories assigned in a class body return `Any` | 4 | item 19 |
| Uncategorized | 420 | item 21 |

### By rule

| Rule | Hits | Package | Tests | Examples | Scripts |
| --- | --- | --- | --- | --- | --- |
| `reportArgumentType` | 451 | 25 | 421 | 5 | 0 |
| `reportAttributeAccessIssue` | 291 | 26 | 264 | 1 | 0 |
| `reportIncompatibleVariableOverride` | 194 | 2 | 169 | 23 | 0 |
| `reportExplicitAny` | 116 | 76 | 25 | 13 | 2 |
| `reportIncompatibleMethodOverride` | 76 | 5 | 66 | 5 | 0 |
| `reportReturnType` | 46 | 0 | 45 | 1 | 0 |
| `reportFunctionMemberAccess` | 25 | 4 | 19 | 2 | 0 |
| `reportAssignmentType` | 23 | 0 | 20 | 3 | 0 |
| `reportUnnecessaryIsInstance` | 20 | 20 | 0 | 0 | 0 |
| `reportCallIssue` | 18 | 1 | 16 | 1 | 0 |
| `reportDeprecated` | 14 | 5 | 9 | 0 | 0 |
| `reportIndexIssue` | 11 | 0 | 11 | 0 | 0 |
| `reportUnsafeMultipleInheritance` | 9 | 4 | 3 | 2 | 0 |
| `reportUnknownParameterType` | 9 | 1 | 8 | 0 | 0 |
| `reportMissingSuperCall` | 8 | 2 | 6 | 0 | 0 |
| `reportUnreachable` | 7 | 5 | 2 | 0 | 0 |
| `reportGeneralTypeIssues` | 7 | 1 | 6 | 0 | 0 |
| `reportUndefinedVariable` | 7 | 0 | 7 | 0 | 0 |
| `reportMissingParameterType` | 5 | 0 | 5 | 0 | 0 |
| `reportPropertyTypeMismatch` | 4 | 4 | 0 | 0 | 0 |
| `reportUnnecessaryComparison` | 4 | 4 | 0 | 0 | 0 |
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
| `tests/rest_framework/test_resolvers.py` | 73 |
| `tests/utils/test_querysets.py` | 71 |
| `tests/rest_framework/test_sets.py` | 55 |
| `tests/rest_framework/test_converter.py` | 48 |
| `tests/test_resource_policy.py` | 38 |
| `tests/test_views.py` | 38 |
| `tests/test_django_patches.py` | 36 |
| `tests/test_routers.py` | 33 |
| `tests/test_list_field.py` | 29 |
| `examples/fakeshop/apps/library/serializers.py` | 26 |


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
