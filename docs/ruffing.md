# Ruffing: to-do list

ruff 0.17.0 lints and formats every tracked Python file (513, the same set `git ls-files '*.py'` lists), configured in
`pyproject.toml` `[tool.ruff]`. This file tracks the rules switched on, the rules still off, the config-level ignores
and the `# noqa` comments still in the tree.
A rule family is selected whole. Every stable code is on except the off-by-design block of `ignore`; the ratchet
block is empty. A site the rule is wrong about carries a `# noqa: CODE - reason`; a whole folder the rule is wrong
about gets a per-file ignore with its reason in `pyproject.toml`.

Progress: 39 done, 0 to do. Stable rules: 815, every one named in the config: 806 on, 9 in `ignore` (off by
design). The 139 preview-only rules stay off with `preview`. `# noqa` comments: 388 lines in 109 files.

Counts below were measured on ruff 0.17.0 at ee9c8161 (items 1-27), 8ca6a481 (items 28-35) and the tree after
e42952a5 (items 36-37), fa4182a9 (item 31), ee1a2367 (item 38) and 1cf08608 (item 39). "Root" is `conftest.py`, `line_count.py` and `docs/dry/export_dry_review.py`.

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
- [x] 36. `D400`, `D404` (7 summaries reworded) and `D401` (every function summary in the imperative mood) on,
  each selected by code, since the Google convention drops all three from a `D` prefix select;
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

- [x] 31. The tests/ and examples/ per-file ignores shrunk from 21 and 14 codes to 12 and 7 (plus `D102` / `D103`
  on `test_*.py`, `D` on the generated migrations and `UP031` on `test_query/`). `ANN`: ruff's fix wrote 8370 return
  types (`-> None` on every test), about 1750 more were annotated by hand (no `Any`; `@contextmanager` helpers are
  `Generator[...]`, raise-only helpers `NoReturn`). `ARG`: unused lambda and positional stand-in parameters are
  `_`-prefixed; a parameter a framework passes by keyword is `del`eted, which retires 45 `reportUnusedParameter`
  ignores. `B018`: `_ = expr`. `D`: every formatting rule is on, and `D1` is on except `D106` (`class Meta:`); the
  example Filter / Order / Admin / AppConfig / Command classes and Query resolvers carry docstrings. `E501`: 6 `noqa`
  on `path::Symbol` citations that cannot wrap. `ERA001`: prose reworded; pseudo blocks kept verbatim inside a
  `# ruff: disable[ERA001]` / `# ruff: enable[ERA001]` fence (9). `FBT`: parametrized bools follow a bare `*`,
  helpers take their flag by keyword; 15 `noqa` where the bool is the value under test or mirrors Django's positional
  `execute_wrapper`. `N802`: one rename, 4 `noqa`. `PERF`, `RUF043` (raw strings; three loose patterns tightened),
  `SIM117` fixed at every site. The four `tests/test_django_patches.py` upstream-shape methods stay unannotated inside
  a `# ruff: disable[ANN206]` fence: `inspect.getsource` of the two accepted shapes must match Django's source byte for
  byte, and the two rejected shapes differ from an audited body only in the drift under test
- [x] 38. Four off-by-design codes turned on. `D413`: selected by code (the Google preset drops it), 79 safe fixes.
  `TC001`-`TC003`: 164 imports in the package, scripts/ and root moved under `TYPE_CHECKING` (14 annotations quoted in
  the 8 files without `from __future__ import annotations`); `exempt-modules` adds `strawberry` (a resolver's `Info`
  is detected by its annotation at schema build), and `runtime-evaluated-decorators` / `-base-classes` name the
  Strawberry decorators and `DjangoType`; tests/ and examples/ keep the per-file ignore. `PLR2004`: the 18 package
  hits refactored (`HTTPStatus.OK`, `utils/_narrowing.py::is_exact_pair`, `match` destructuring, named upstream
  arities); tests/, examples/ and scripts/ keep the per-file ignore. `TID252`: 937 parent-relative imports made
  absolute (`ban-relative-imports = "parents"` stated; siblings stay relative); 4 source-text test assertions
  follow. `debug_toolbar.py` drops 2 `E402` with its typing-only imports
- [x] 39. `PLC0415` on (2074 hits). Hoisted to module top wherever the import's timing did not matter, checked by
  importing every package module in a fresh interpreter (the import fingerprint and the
  `import django_strawberry_framework` module set unchanged) and by the suite; tests that patched a source module
  now patch the binding the consumer holds. Example tests read reloaded schema classes off the module object
  (`library_schema.BookType`; `schema_reload` reloads in place) instead of a call-time `from ... import BookType`.
  `banned-module-level-imports` (`TID253`) names the fakeshop top-level modules (`apps`, `config`, `schema_reload`,
  `strategy_schemas`): scripts import them only after `bootstrap_fakeshop_django`, which exempts those 26 sites
  from `PLC0415`, and the package can never import the example project; tests/ and examples/ per-file-ignore
  `TID253`. 59 sites stay local with `# noqa: PLC0415 - reason`: package 49 (21 import cycles, 9 finalizer subsystem
  binds, 8 Channels and 1 DRF soft dependency, 4 `orders` / `filters` kept out of the root import graph, 4 patch
  modules loaded in `ready()`, 2 lazily-resolved names), tests 7, scripts 2, root 1

## Still ignored in tests/ and examples/

| Code | Tests | Examples | Why |
| --- | --- | --- | --- |
| `S101` | 15782 | 5997 | assert is the pytest idiom |
| `RUF012` | 1002 | 317 | Meta `fields = {...}` / `[...]`, `permission_classes = [...]` and Django `Meta.ordering` are the consumer idiom; a `ClassVar` annotation is not what a consumer writes |
| `D102`, `D103` (`test_*.py` only) | 887 | 290 | the test name is the summary; most tests carry a contract docstring, the rest are not required to |
| `D401` | 239 | 133 | a test docstring states the contract declaratively ("A two-bound range applies ...") |
| `D106` | 12 | 239 | every site is `class Meta:` |
| `N806` | 193 | 0 | a class built by `type(...)` or a factory binds to a PascalCase local |
| `DJ008` | 128 | 0 | throwaway test models |
| `D` (migrations only) | 0 | 63 | `makemigrations` writes them |
| `SLOT000`, `SLOT001` | 64 | 3 | hostile `str` / `tuple` subclasses model consumer values with an instance `__dict__` |
| `UP031` (`test_query/` only) | 0 | 48 | GraphQL query text is all braces; `str.format` / f-strings would double them |
| `S105`, `S106`, `S107` | 15 | 27 | fixture credentials and the example's dev `SECRET_KEY` |
| `S603`, `S607` | 32 | 0 | fixed argv of git / `sys.executable` |
| `TC001`, `TC002`, `TC003` | 276 | 160 | strawberry / `DjangoType` classes built inside functions, mostly without `from __future__ import annotations`; the fix would quote about 790 annotations |
| `PLR2004` | 442 | 794 | assertions compare against literal expected values |

scripts/ keeps `PERF` (16 sites), `S603` / `S607` (40) and `PLR2004` (25).

## Rules still off

Off by design (not planned):

- `SLF001` (2559, private member access): the package shares underscore names across its modules
  (`reportPrivateUsage` is off for the same reason)
- `EM101`, `EM102`, `TRY003` (3097): exception-message style only
- `FIX002` (10), `TD003` (10): a TODO is the `TODO(spec-NNN slice N): ...` anchor convention, which names a spec or
  a backlog entry, not an issue link; the rest of `TD` and `FIX` is on
- `CPY001` (513, copyright headers)
- `D203`, `D213`: the opposites of `D211` and `D212`, which the Google convention selects (ruff drops one of each
  pair)

## Files ruff skips

None that it should check. `ruff check --show-files` lists exactly the 513 tracked Python files. The files it skips
are git-ignored scratch trees (`docs/shadow/`, cycle temp files, `.venv/`, `.claude/worktrees/`), read through
ruff's default `respect-gitignore`. `[tool.ruff.format]` excludes `*.md`: fenced Python in Markdown is verbatim example
content, so the formatter owns `.py` only. No file carries a file-level `# ruff: noqa`.

## Config ignores

Global `ignore`: the off-by-design block only (9): `CPY001`, `D203`, `D213`, `EM101`, `EM102`, `FIX002`, `SLF001`,
`TD003`, `TRY003`. Rule settings: `logger-objects` (the
package logger, for `BLE001` / `LOG`), `flake8-annotations.allow-star-arg-any`, `flake8-import-conventions.aliases`
(ruff's map minus `datetime = dt`), `flake8-tidy-imports.ban-relative-imports = "parents"` and
`banned-module-level-imports` (the fakeshop top-level modules, item 39), `flake8-type-checking`
(`quote-annotations`, `runtime-evaluated-decorators`, `runtime-evaluated-base-classes`, `exempt-modules`),
`pep8-naming.classmethod-decorators` (Django's `classonlymethod`), and the
`mccabe` / `pylint` complexity ratchets of item 36.

Per-file ignores:

| Glob | Codes |
| --- | --- |
| `tests/**/*.py` | `D106`, `D401`, `N806`, `RUF012`, `S101`, `DJ008`, `SLOT000`, `SLOT001`, `S106`, `S107`, `S603`, `S607`, `TC001`-`TC003`, `PLR2004`, `TID253` |
| `examples/**/*.py` | `D106`, `D401`, `RUF012`, `S101`, `SLOT000`, `S105`, `S106`, `TC001`-`TC003`, `PLR2004`, `TID253` |
| `conftest.py` | `TID253` |
| `tests/**/test_*.py`, `examples/**/test_*.py` | `D102`, `D103` |
| `examples/**/migrations/*.py` | `D` |
| `scripts/**/*.py` | `PERF`, `T201`, `INP001`, `S603`, `S607`, `PLR2004` |
| `line_count.py` | `T201` |
| `docs/dry/export_dry_review.py` | `T201`, `INP001` |
| `examples/fakeshop/*.py`, `examples/fakeshop/tests/*.py` | `INP001` |
| `examples/fakeshop/test_query/**/*.py` | `INP001`, `UP031` |

## Custom formatter interplay

`scripts/check_trailing_commas.py` (hook `source-layout`, CI `--check`) and ruff share one pipeline, in this
order: the script `--fix`, `ruff check --fix`, `ruff format`. The script's `--fix` runs `ruff format` on the files
it rewrote and repeats comma edit plus format until nothing changes (`MAX_FIX_ROUNDS`, 3); a file still changing
after that is an `unfixable` error, never a pass. No ruff rule and the script rewrite each other: the pipeline
reaches a fixpoint, and the script's `--check` is clean after ruff's fixes. What each side owns:

- Single-line collection and signature layout belongs to the script: explode at 4 items (2 in `models.py`),
  collapse below that when the one-line form fits `[tool.ruff] line-length` (99, not E501's 110), measured in
  ruff's display columns (an emoji is two). `COM812` only adds commas to constructs that are already multi-line;
  `COM819` never survives the script's own format pass.
- Imports belong to isort and the formatter: `split-on-trailing-comma` (the default) keeps a parenthesized import
  exploded after a trailing comma. Imports are not a script construct and have no threshold.
- `.py` string literals, docstrings (`D2xx` / `D4xx`) and quotes (`Q`) are out of the script's reach.
- The script's ASCII check is stricter than `RUF001`-`RUF003` (it also rejects accented letters), which stay on;
  only emoji pass both.

Suppressions go on the element. The script refuses to explode a line that ends in `# noqa`,
`# pyright: ignore` or `# type: ignore`: after the explode the comment would sit after the closing bracket while
the diagnostic moves to an element line, so `RUF100` would delete the noqa and basedpyright would report the
ignore as unnecessary. `--check` reports it as not fixable and `--fix` as an `unfixable` error; move the comment
onto the element it silences.

Ruff-side notes:

- The hug form `(\n    a, b, c\n)` that `ruff format` writes after a lengthening autofix (a `TC` quote, a
  `TID252` absolute import) needs `ruff check --fix` (`COM812`) and `ruff format` run twice. That is ruff against
  itself; the script is not involved.
- Collapsing a wrapped implicit concatenation in a below-threshold collection makes `ISC001` fire; its fix joins
  the strings in the same pass.
- After any `--unsafe-fixes` pass, rerun the whole pipeline script first: `PLR1714`, `SIM101` and `C4` can write a
  single-line 4-item literal.

Rules: the `TC`, `TID252` and `D413` autofixes (item 38) and the planned `EM` autofix and `CPY001` header were
measured against the pipeline with no ping-pong. A `CPY001` header would have to be emitted by
`scripts/build_kanban_tracked_path_constants.py::render_constants`, since the module it generates passes the same
pipeline.

## `# noqa` breakdown

Lines carrying `# noqa`: 388 (none bare) in 109 files: package 244, tests 76, examples 56, scripts 8, root 4.

| Code | Hits | Package | Tests | Examples | Scripts / root | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `BLE001` | 112 | 109 | 1 | 1 | 1 | deliberate containment whose fallback or flavor a shared helper cannot carry |
| `PLC0415` | 59 | 49 | 7 | 0 | 3 | an import cycle, an optional dependency, a subsystem bound only when imported, or a name resolved lazily (item 39) |
| `A002` | 55 | 9 | 0 | 46 | 0 | a `filter` / `id` parameter that is the GraphQL argument name or a public keyword |
| `ANN401` | 21 | 21 | 0 | 0 | 0 | an `Any` the package does not own, each with a basedpyright reason |
| `PLC0414` | 11 | 11 | 0 | 0 | 0 | explicit re-exports basedpyright needs |
| `FBT003` | 15 | 0 | 15 | 0 | 0 | the bool is the value under test, or mirrors Django's positional `execute_wrapper` |
| `N802` | 14 | 10 | 4 | 0 | 0 | PascalCase field factories (`DjangoConnectionField`, ...), for graphene-django parity, unittest vocabulary, a camelCase wire name |
| `S102` | 10 | 0 | 10 | 0 | 0 | `exec` of a literal program the test runs |
| `N815` | 9 | 0 | 6 | 3 | 0 | camelCase model fields the naming tests need |
| `DJ001`, `S301`, `S610` | 11 | 0 | 10 | 1 | 0 | NULL as fixture input, the one `pickle` round trip, hostile `.extra()` input |
| `F821` | 7 | 0 | 7 | 0 | 0 | forward references the definition-order tests leave unresolved |
| `E501` | 6 | 0 | 4 | 2 | 0 | a `path::Symbol` citation wider than the limit on its own line |
| `N805`, `N818` | 6 | 4 | 2 | 0 | 0 | metaclass methods take `cls`; control-flow exceptions |
| `B009`, `B004`, `B010`, `B904`, `TRY004` | 10 | 10 | 0 | 0 | 0 | `getattr` / `setattr` past the stubs, a `__call__` probe, `raise` chaining, `ValueError` for bad input |
| `S101`, `S608`, `PT009`, `PLW0603`, `PYI034`, `FBT001`, `RUF012` | 15 | 15 | 0 | 0 | 0 | django-filter's asserts, the lateral SQL, the unittest mixin, patched module caches, a metaclass `__new__`, Django's positional `many`, a stub-typed list |
| `E402`, `PERF203`, `RUF063`, `FBT002`, `TRY301`, `PTH115`, others | 22 | 6 | 7 | 3 | 6 | one to three each |

### Most `# noqa` per file

| File | Lines |
| --- | --- |
| `examples/fakeshop/apps/kanban/schema.py` | 23 |
| `django_strawberry_framework/types/finalizer.py` | 18 |
| `django_strawberry_framework/utils/relations.py` | 14 |
| `django_strawberry_framework/exceptions.py` | 12 |
| `django_strawberry_framework/utils/errors.py` | 12 |
| `examples/fakeshop/apps/glossary/schema.py` | 10 |
| `tests/types/test_definition_order.py` | 10 |
| `django_strawberry_framework/auth/mutations.py` | 10 |
| `django_strawberry_framework/utils/querysets.py` | 9 |
| `django_strawberry_framework/testing/client.py` | 8 |

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
- The per-file ignores are policy calls: `DJ008`, `SLOT000` / `SLOT001`, `S105`-`S107` for tests/ and
  examples/, `S603` / `S607` for tests/ and scripts/. The alternatives were 127 `__str__`s, 62 `__slots__ = ()`, and
  about 115 `noqa` lines.
- Item 31 passes the default (SQLite) suite at 100% coverage, ruff, format, `check_trailing_commas.py`, basedpyright
  (main and floor), `check_citations.py` and the `TREE.md` render; the Postgres tier was not run.
- AGENTS.md's `ERA001` line now prescribes the `# ruff: disable[ERA001]` / `enable` fence instead of a per-line
  `noqa`, since ruff exempts only the `TODO` line itself. Keep that wording?
- `D102` / `D103` on test functions: 1177 test functions have no docstring (most of the others carry a contract
  docstring). Turning the rule on means writing 1177 true contract docstrings. Keep ignored?
- `N806`: the 82 PascalCase class bindings in tests could be renamed lowercase, which reads as instances. Keep
  ignored?
- `tests/forms/test_sets.py`: annotating `_item_model_form` widened one existing ignore on the hostile
  `form_cls._meta.model = "Item"` line to `reportAttributeAccessIssue, reportGeneralTypeIssues`.

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
