# Ruffing: to-do list

ruff 0.17.0 lints and formats every tracked Python file (511, the same set `git ls-files '*.py'` lists), configured in
`pyproject.toml` `[tool.ruff]`. This file tracks the rules switched on, the rules still off, the config-level ignores
and the `# noqa` comments still in the tree.
A rule family is selected whole. Every stable code is on except the off-by-design block of `ignore`; the ratchet
block is empty. A site the rule is wrong about carries a `# noqa: CODE - reason`; a whole folder the rule is wrong
about gets a per-file ignore with its reason in `pyproject.toml`.

Progress: 36 done, 1 to do (item 31). Stable rules: 815, every one named in the config: 799 on, 16 in `ignore` (off
by design). The 139 preview-only rules stay off with `preview`. `# noqa` comments: 302 lines in 91 files.

Counts below were measured on ruff 0.17.0 at ee9c8161 (items 1-27), 8ca6a481 (items 28-35) and the tree after
e42952a5 (items 36-37). "Root" is `conftest.py`, `line_count.py` and `docs/dry/export_dry_review.py`.

## Done: rules on

- [x] 1. `E`, `W` (pycodestyle): the formatter wraps at 99; `E501` flags only lines past 110 (`max-line-length`)
- [x] 2. `F` (Pyflakes)
- [x] 3. `I` (isort), with `django_strawberry_framework` first-party
- [x] 4. `UP` (pyupgrade), targeting py310
- [x] 5. `ANN` (annotations); tests/ and examples/ exempt
- [x] 6. `D` (pydocstyle, Google convention); tests/ and examples/ exempt
- [x] 7. `A` (builtins)
- [x] 8. `ARG` (unused arguments), `*args` / `**kwargs` padding exempt (`ignore-variadic-names`); tests/ and examples/
  exempt
- [x] 9. `ASYNC` (blocking calls in async code)
- [x] 10. `B` (bugbear)
- [x] 11. `N` (pep8-naming)
- [x] 12. `C4` (comprehensions)
- [x] 13. `ERA` (commented-out code); TODO-anchored pseudo blocks exempt
- [x] 14. `FLY` (static `str.join` to f-string)
- [x] 15. `PERF` (Perflint); tests/, examples/ and scripts/ exempt
- [x] 16. `Q` (double quotes) and `RSE` (raise hygiene)
- [x] 17. `RUF` (Ruff-specific, `RUF100` unused-noqa and `RUF001`-`RUF003` ambiguous Unicode included)
- [x] 18. `SIM` (simplify)
- [x] 19. `COM` (trailing commas; `COM812` pairs with `scripts/check_trailing_commas.py`) and `ISC` (implicit
  concatenation). ruff 0.17 reports a formatter conflict for `COM812` only
- [x] 20. `PL` (Pylint), minus the off-by-design codes below
- [x] 21. Every other stable rule with no site today, by selecting its family: `DJ`, `DTZ`, `EXE`, `FA`, `FIX`,
  `FURB`, `G`, `ICN`, `INT`, `LOG`, `PGH`, `PIE`, `PT`, `PTH`, `PYI`, `RET`, `S`, `SLOT`, `T10`, `TC`, `TD`, `TID`,
  `TRY`, `YTT`. The codes that reported were ratcheted in items 28-35
- [x] 22. Dead config ignores deleted: `ANN002`, `ANN003`, `D417`, `RUF001`-`RUF003` from the global `ignore`; `F841`
  and `SIM118` from the tests/ and examples/ lists; `N806`, `B018` and `PERF` from the examples/ list; the
  `__init__.py`, `**/migrations/*.py`, `**/views.py`, `**/urls.py` and `**/admin.py` entries
- [x] 23. `T201` (print) on for everything but scripts/ and the root tools (`line_count.py`,
  `docs/dry/export_dry_review.py`), where print is the CLI output
- [x] 24. Every remaining family selected, so the config names every stable rule: `AIR`, `FAST`, `NPY`, `PD` (on,
  silent unless their library is imported), `BLE`, `C90`, `CPY`, `EM` (`EM103` on), `FBT`, `INP`, `SLF`; and `D204`,
  `D215`, `D406`-`D409`, which sit outside the Google convention and report nothing
- [x] 25. `ISC004` (84 implicit concatenations inside a list or tuple, each a wrapped single string, none a missing
  comma; now parenthesized) and `PYI055` (32 `type[A] | type[B]` annotations rewritten as `type[A | B]`)
- [x] 26. `ICN001` (import aliases), with ruff's default alias map minus `datetime = dt` (the project imports
  `datetime` plainly), and `INP001` (missing `__init__.py`), with per-file ignores for the folders that deliberately
  have none: scripts/, `docs/dry/export_dry_review.py`, fakeshop's top-level modules, `examples/fakeshop/tests/` and
  `examples/fakeshop/test_query/`
- [x] 27. `TD002`, `TD004`, `TD005` (TODO author, colon, description): the six `TODO(BACKLOG ...)` /
  `TODO(unscheduled ...)` anchors now carry their whole head and `):` on the first line with the description after
  it, and the card-id notes in `examples/fakeshop/apps/products/schema.py` sit on their own `# needs TODO-BETA-...:`
  line above the commented-out code they gate
- [x] 28. The small real-signal codes (about 340 sites), fixed at the root: composite asserts split (`PT018`),
  side-effect fixtures moved to `@pytest.mark.usefixtures` or renamed where the test reads the value (`PT019`),
  `match=` on every `raises` / `warns` (`PT011`, `PT030`), one statement under each `raises` (`PT012`), plain asserts
  for unittest ones (`PT009`, `PT027`), `PT006`/`PT007`/`PT013`/`PT017`/`PT022`; needless lambdas inlined (`PLW0108`),
  `__hash__ = None` beside each `__eq__` (`PLW1641`), loop variables kept (`PLW2901`), `check=False` spelled out
  (`PLW1510`); `PYI034` / `PYI036`, `TRY300` / `TRY301` (a raising check moved into a named helper, guarded work kept
  inside the `try`), `PLC0105` / `PLC0207`, `PLR0402` / `PLR1711` / `PLR1714`, `RET`, `PTH`, `FURB`, `PIE`, `DTZ`,
  `EXE001` (four script shebangs deleted, `manage.py` made executable). Kept with a `noqa`: lambdas whose late binding
  or factory-vs-class distinction is the point, the `GraphQLTestMixin` delegating to its host `TestCase`
  (`PT009`), `os.readlink` where `Path.readlink()` would normalize the link text (`PTH115`)
- [x] 29. `DJ012` (model bodies reordered), `DJ001` (`noqa` where NULL is the value under test, and `Book.subtitle`,
  where NULL means no subtitle). `DJ008` (127 throwaway test models) and `SLOT000` / `SLOT001` (hostile `str` /
  `tuple` fixtures that model consumer values) are per-file ignores for tests/ (and `SLOT000` for examples/)
- [x] 30. Security and boundaries. `S324` gets `usedforsecurity=False`, `S108` `tempfile` / `tmp_path`, the
  workspace `databases()` SQL is static with Python filtering, `S110` / `S112` return from the handler or move into a
  helper. `S603` / `S607` (fixed argv of git, uv, ruff, `sys.executable`) are per-file ignores for tests/ and
  scripts/; `S105` / `S106` / `S107` (fixture credentials and name-heuristic hits) for tests/ and examples/. `noqa`
  with a reason: `pickle` round trips, `exec` of literal test programs, hostile `.extra()` input, the quoted lateral
  SQL, a seeded demo `random.Random`, the compose container's password, the four `filters/sets.py` asserts that
  mirror django-filter. `BLE001`: `logger-objects` names the re-exported package logger, which clears the 48 handlers
  that log; three narrow to the type actually raised, and the other 148 are deliberate containment and carry one of five reasons (`hostile object, contained by
  design`, `consumer code may raise anything`, `boundary fails closed`, `rewrapped as the typed rejection`,
  `worker thread reports to the main thread`), so `rg "noqa: BLE001 - hostile"` is the census
- [x] 32. `ANN401`: `allow-star-arg-any` clears the `*args: Any, **kwargs: Any` forwards; the other 24 explicit `Any`s
  each carry a basedpyright reason and a `noqa`. `D107`: every `__init__` documented
- [x] 33. `FBT002` (boolean default positional argument): `utils/relations.py::relation_bool`'s `default` is
  keyword-only, and its 7 callers that passed the default `False` positionally drop it; the 3 `conftest.py`
  `_django_db_signature` sites take `noqa: FBT002`, since it mirrors pytest-django's positional
  `django_db(transaction, reset_sequences, ...)` signature on purpose
- [x] 34. `FBT001`: every package and script flag is keyword-only and passed by name, except `write_transaction.py`'s
  two `many` parameters, which Django's `execute_wrapper` passes positionally (`noqa`)
- [x] 35. `FBT003`: the remaining positional `True` / `False` arguments are passed by name
- [x] `PLC0414`: `permissions.py` gets an `__all__`; the eleven `x as x` re-exports basedpyright needs for consumers
  that import through the converter modules, `utils.inputs`, `types.relay` and `filters.base` keep the alias with a
  `noqa`
- [x] 36. `D400`, `D404` (7 summaries reworded) and `D401` (every function summary in the imperative mood) on;
  `C901` and `PLR0911` / `PLR0912` / `PLR0913` / `PLR0915` / `PLR0917` on as ratchets at today's maxima
  (`mccabe.max-complexity` 45, `pylint.max-branches` 39, `max-returns` 20, `max-args` 18, `max-statements` 133,
  `max-positional-args` 10): no new function may exceed the worst one, and lowering a threshold lists the functions
  above it
- [x] 37. `# noqa` refactored away (410 to 302 lines): the package logger lives in the leaf module `_logger.py`, so
  `__init__` needs no `E402`, and `debug_toolbar.py` keeps it only on its three toolbar imports; containment goes
  through `exceptions.py::_safe_attr` / `_safe_call` / `_safe_predicate`, merged guards and `contextlib.suppress` on
  the two last-resort passes (`BLE001` 148 to 112); positional `id` parameters are `id_` and `DjangoNodeField` binds
  `id_` to the wire `id` through `strawberry.argument(name="id")` (`A002`); `pep8-naming.classmethod-decorators` names
  Django's `classonlymethod` (`N805`); one 3-arg `getattr` against `utils/typing.py::MISSING_ATTRIBUTE` replaces
  `hasattr` + `getattr` (`B009`); `tests/_idioms.py` `pickle_roundtrip` and `run_capturing` hold the single `S301` and
  the single test `BLE001`; extension factories are `functools.partial` (`PLW0108`); unused parameters are `del`eted (`ARG`)

## To do: rules still off

- [ ] 31. Shrink the tests/ and examples/ per-file ignores. What each code hides today:

  | Code | Hidden | Tests | Examples |
  | --- | --- | --- | --- |
  | `ANN` (`ANN201`, `ANN202`, `ANN204`, `ANN206`, `ANN205`) | 10066 | 8111 | 1955 |
  | `D` (`D103`, `D106`, `D101`, `D102`, `D205`, `D202`, ...) | 1976 | 1133 | 843 |
  | `RUF012` (mutable class default) | 1310 | 994 | 316 |
  | `ARG` | 405 | 222 | 183 |
  | `N806` | 195 | 195 | 0 |
  | `E501` | 150 | 99 | 51 |
  | `DJ008` | 127 | 127 | 0 |
  | `SIM117` (nested `with`) | 105 | 98 | 7 |
  | `RUF043` (`match=` metacharacters) | 94 | 91 | 3 |
  | `SLOT000`, `SLOT001` | 62 | 59 | 3 |
  | `UP031` (printf formatting) | 48 | 0 | 48 |
  | `S106`, `S105`, `S107` | 42 | 15 | 27 |
  | `ERA001` | 36 | 15 | 21 |
  | `B018` | 35 | 35 | 0 |
  | `S603`, `S607` | 32 | 32 | 0 |
  | `N802` | 6 | 6 | 0 |
  | `PERF` | 3 | 3 | 0 |

  scripts/ drops `PERF` (16 sites) and `S603` / `S607` (40).

Off by design (not planned):

- `PLC0415` (2081, import outside top level): import cycles are broken by local imports
- `TC001`-`TC003` (607): Strawberry and Django read annotations at run time, so a typing-only import would be a
  `NameError`
- `SLF001` (2559, private member access): the package shares underscore names across its modules
  (`reportPrivateUsage` is off for the same reason)
- `TID252` (917, relative imports): the package imports its siblings relatively
- `EM101`, `EM102`, `TRY003` (3097): exception-message style only
- `PLR2004` (1276, magic value in comparison): 1235 of them are test and example assertions
- `FIX002` (10), `TD003` (10): a TODO is the `TODO(spec-NNN slice N): ...` anchor convention, which names a spec or
  a backlog entry, not an issue link; the rest of `TD` and `FIX` is on
- `CPY001` (511, copyright headers)
- `D203`, `D213`: the opposites of `D211` and `D212`, which the Google convention selects (ruff drops one of each
  pair)
- `D413` (71, blank line after the last section): the Google convention ends a docstring right after its last
  section, and ruff's `google` preset turns `D413` off

## Files ruff skips

None that it should check. `ruff check --show-files` lists exactly the 511 tracked Python files. The files it skips
are git-ignored scratch trees (`docs/shadow/`, cycle temp files, `.venv/`, `.claude/worktrees/`), read through
ruff's default `respect-gitignore`. `[tool.ruff.format]` excludes `*.md`: fenced Python in Markdown is verbatim example
content, so the formatter owns `.py` only. No file carries a file-level `# ruff: noqa`.

## Config ignores

Global `ignore`: the off-by-design block only (16): `CPY001`, `D203`, `D213`, `D413`, `EM101`, `EM102`, `FIX002`,
`PLC0415`, `PLR2004`, `SLF001`, `TC001`-`TC003`, `TD003`, `TID252`, `TRY003`. Rule settings: `logger-objects` (the
package logger, for `BLE001` / `LOG`), `flake8-annotations.allow-star-arg-any`, `flake8-import-conventions.aliases`
(ruff's map minus `datetime = dt`), `pep8-naming.classmethod-decorators` (Django's `classonlymethod`), and the
`mccabe` / `pylint` complexity ratchets of item 36.

Per-file ignores:

| Glob | Codes |
| --- | --- |
| `tests/**/*.py` | `D`, `ANN`, `ERA001`, `SIM117`, `E501`, `N802`, `N806`, `B018`, `RUF012`, `PERF`, `RUF043`, `ARG`, `S101`, `FBT`, `DJ008`, `SLOT000`, `SLOT001`, `S106`, `S107`, `S603`, `S607` |
| `examples/**/*.py` | `D`, `ANN`, `ERA001`, `SIM117`, `E501`, `UP031`, `RUF012`, `RUF043`, `ARG`, `S101`, `FBT`, `SLOT000`, `S105`, `S106` |
| `scripts/**/*.py` | `PERF`, `T201`, `INP001`, `S603`, `S607` |
| `line_count.py` | `T201` |
| `docs/dry/export_dry_review.py` | `T201`, `INP001` |
| `examples/fakeshop/*.py`, `examples/fakeshop/tests/*.py`, `examples/fakeshop/test_query/**/*.py` | `INP001` |

## `# noqa` breakdown

Lines carrying `# noqa`: 302 (none bare) in 91 files: package 197, tests 43, examples 54, scripts 4, root 4.

| Code | Hits | Package | Tests | Examples | Scripts / root | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `BLE001` | 112 | 109 | 1 | 1 | 1 | deliberate containment whose fallback or flavor a shared helper cannot carry |
| `A002` | 55 | 9 | 0 | 46 | 0 | a `filter` / `id` parameter that is the GraphQL argument name or a public keyword |
| `ANN401` | 21 | 21 | 0 | 0 | 0 | an `Any` the package does not own, each with a basedpyright reason |
| `PLC0414` | 11 | 11 | 0 | 0 | 0 | explicit re-exports basedpyright needs |
| `N802` | 10 | 10 | 0 | 0 | 0 | PascalCase field factories (`DjangoConnectionField`, ...), for graphene-django parity, and unittest vocabulary |
| `S102` | 10 | 0 | 10 | 0 | 0 | `exec` of a literal program the test runs |
| `N815` | 9 | 0 | 6 | 3 | 0 | camelCase model fields the naming tests need |
| `DJ001`, `S301`, `S610` | 11 | 0 | 10 | 1 | 0 | NULL as fixture input, the one `pickle` round trip, hostile `.extra()` input |
| `F821` | 7 | 0 | 7 | 0 | 0 | forward references the definition-order tests leave unresolved |
| `N805`, `N818` | 6 | 4 | 2 | 0 | 0 | metaclass methods take `cls`; control-flow exceptions |
| `B009`, `B004`, `B010`, `B904`, `TRY004` | 10 | 10 | 0 | 0 | 0 | `getattr` / `setattr` past the stubs, a `__call__` probe, `raise` chaining, `ValueError` for bad input |
| `S101`, `S608`, `PT009`, `PLW0603`, `PYI034`, `FBT001`, `RUF012` | 15 | 15 | 0 | 0 | 0 | django-filter's asserts, the lateral SQL, the unittest mixin, patched module caches, a metaclass `__new__`, Django's positional `many`, a stub-typed list |
| `E402`, `PERF203`, `RUF063`, `FBT002`, `TRY301`, `PTH115`, others | 25 | 8 | 7 | 3 | 7 | one to three each |

### Most `# noqa` per file

| File | Lines |
| --- | --- |
| `examples/fakeshop/apps/kanban/schema.py` | 23 |
| `django_strawberry_framework/utils/relations.py` | 14 |
| `django_strawberry_framework/exceptions.py` | 12 |
| `django_strawberry_framework/utils/errors.py` | 11 |
| `examples/fakeshop/apps/glossary/schema.py` | 10 |
| `django_strawberry_framework/utils/querysets.py` | 9 |
| `django_strawberry_framework/mutations/sets.py` | 8 |
| `django_strawberry_framework/testing/client.py` | 8 |
| `tests/types/test_definition_order.py` | 8 |
| `django_strawberry_framework/auth/mutations.py` | 7 |

## Waiting on You

- Run the `FAKESHOP_PG_DSN` tier. Both suppression sweeps pass ruff, `ruff format`, `check_trailing_commas.py`,
  basedpyright (main and floor), `check_public_types.py`, `check_citations.py`, the render checks and the default
  (SQLite) pytest run at 100% coverage; the Postgres tier was not run. Riskiest: the `exceptions.py` containment helpers and merged guards (`types/definition.py`, `utils/relations.py`,
  `utils/errors.py`, `exceptions.py`), `FilterSet._build_stashed_instance`, the `usefixtures` / `django_db` mark moves
  (13 registry-isolation modules, the fakeshop `db` / `transactional_db` fixtures), the typed hostile doubles
  (`test_consumers.py`, `test_list_field.py`, `test_error_policy.py`, `optimizer/test_hints.py`), and the typed
  `argparse` namespaces in every script and `docs/dry/export_dry_review.py`, and the root `conftest.py`, whose
  Postgres connection-tracking wrapper changed shape.
- `consumers.py`: 38 handlers re-raise `(CancelledError, KeyboardInterrupt, SystemExit)` and then catch
  `BaseException`, which swallows `GeneratorExit` from a coroutine closed mid-await (then `RuntimeError: coroutine
  ignored GeneratorExit`). Narrowing them to `except Exception` is a behavior change that wants its own card and a
  `GeneratorExit` regression test.
- `extensions/error_policy.py` `on_operation`'s last resort is now `contextlib.suppress(Exception)`; logging it
  instead would surface a failed store that today serves the unmasked result silently. Log it?
- `types.relay.SyncMisuseError` and `filters.base.LazyRelatedClassMixin` are back-compat re-export paths nothing in the
  repo imports (both names live on the package root and their owner modules). Drop them?
- The 46 example `filter:` resolver parameters (`A002`): a fakeshop-level Strawberry `NameConverter` that strips a
  trailing `_` would let them read `filter_` with the wire name unchanged, but `FilterInput`'s docstring prescribes
  `filter:` for consumers. Adopt the converter in the example project?
- `TC001` / `TC002` / `TC003`: `exempt-modules = ["typing", "typing_extensions", "strawberry.types"]` plus the autofix
  moves 519 imports under `TYPE_CHECKING` with the schema still building; the dynamic `strawberry.type(cls)` paths
  only a full suite run can clear. Do it once you are ready to run the suite after it?
- `TID252` autofixes cleanly (65 files, +172 lines) but leaves sibling imports relative and parent imports absolute;
  judged a wash, so not done.
- AGENTS.md says TODO-anchored pseudo blocks are exempt from `ERA001`; in ruff 0.17 a `# TODO(...)` line does not
  exempt the commented code after it, so the claim is nominal.
- The per-file ignores are policy calls: `DJ008`, `SLOT000` / `SLOT001`, `S105`-`S107` for tests/ and
  examples/, `S603` / `S607` for tests/ and scripts/. The alternatives were 127 `__str__`s, 62 `__slots__ = ()`, and
  about 115 `noqa` lines.
- Two new tracked files: `django_strawberry_framework/_logger.py` and `tests/_django_private.py`; at commit run
  `build_kanban_tracked_path_constants.py` and `build_tree_md.py` (the hook does the first).

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
