# Ruffing: to-do list

ruff 0.17.0 lints and formats every tracked Python file (511, the same set `git ls-files '*.py'` lists), configured in
`pyproject.toml` `[tool.ruff]`. This file tracks the rules switched on, the rules still off, the config-level ignores
and the `# noqa` comments still in the tree.
A rule family is selected whole; a code in it that still reports sits in the ratchet block of `ignore` until its sites
are fixed at the root, gated (`ruff check`, `ruff format --check`, `scripts/check_trailing_commas.py --check`, full
suite at 100% coverage) and committed, and the line is deleted.

Progress: 25 done, 5 to do. Stable rules: 815, every one named in the config: 708 on, 107 in `ignore` (33 off by
design, 74 ratchet). The 139 preview-only rules stay off with `preview`. `# noqa` comments: 160 lines in 52 files.

Counts below were measured on ruff 0.17.0 at ee9c8161. "Root" is `conftest.py`, `line_count.py` and
`docs/dry/export_dry_review.py`.

## Done: rules on

- [x] 1. `E`, `W` (pycodestyle): the formatter wraps at 99; `E501` flags only lines past 110 (`max-line-length`)
- [x] 2. `F` (Pyflakes)
- [x] 3. `I` (isort), with `django_strawberry_framework` first-party
- [x] 4. `UP` (pyupgrade), targeting py310
- [x] 5. `ANN` (annotations), minus `ANN401` (item 30); tests/ and examples/ exempt
- [x] 6. `D` (pydocstyle, Google convention), minus `D107` (item 30); tests/ and examples/ exempt
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
- [x] 20. `PL` (Pylint), minus the off-by-design codes below and the ratchet codes of items 26 and 28
- [x] 21. Every other stable rule with no site today, by selecting its family: `DJ`, `DTZ`, `EXE`, `FA`, `FIX`,
  `FURB`, `G`, `ICN`, `INT`, `LOG`, `PGH`, `PIE`, `PT`, `PTH`, `PYI`, `RET`, `S`, `SLOT`, `T10`, `TC`, `TD`, `TID`,
  `TRY`, `YTT`. The codes that still report are in `ignore` (off by design below, or ratchet items 26-30)
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

## To do: rules still off

Counts are the diagnostics each code reports when its ignore line is deleted (package / tests / examples / scripts /
root).

- [ ] 26. Small, real signal (about 340 sites), each row's codes in the ratchet block:

  | Rule | Sites | Package | Tests | Examples | Scripts | Root | Catches |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | `PT` | 168 | 3 | 128 | 36 | 1 | 0 | composite asserts (56), fixtures injected for their side effect (52), unittest asserts (14), `raises` without `match` (12) or around several statements (12) |
  | `PLW` | 54 | 6 | 41 | 7 | 0 | 0 | `__eq__` without `__hash__` (18), needless lambdas (29), a reassigned loop variable (3) |
  | `PYI034`, `PYI036` | 4 | 3 | 1 | 0 | 0 | 0 | `__new__` / `__exit__` annotations |
  | `TRY300`, `TRY301` | 18 | 14 | 2 | 1 | 1 | 0 | `return` inside `try`, `raise` caught by its own `try` |
  | `PLC` (not `PLC0415`) | 19 | 16 | 2 | 0 | 1 | 0 | needless import alias (12), `split` without `maxsplit` |
  | `PLR0402`, `PLR1711`, `PLR1714` | 17 | 2 | 13 | 2 | 0 | 0 | `import a.b as b`, a trailing `return None`, repeated `==` |
  | `RET` | 15 | 1 | 8 | 6 | 0 | 0 | explicit `return None`, `else` after `return` |
  | `PTH` | 14 | 0 | 1 | 1 | 7 | 5 | `os` / `open` where `pathlib` reads plainer |
  | `FURB` | 10 | 6 | 2 | 0 | 2 | 0 | `x if x else y`, prefix slicing, regex flag aliases |
  | `PIE` | 7 | 3 | 1 | 1 | 1 | 1 | a needless `pass` / `...`, chained `startswith` |
  | `DTZ` | 5 | 0 | 4 | 0 | 1 | 0 | a naive `datetime` / `date.today()` |
  | `EXE001` | 5 | 0 | 0 | 1 | 4 | 0 | a shebang on a file that is not executable |

- [ ] 27. Larger, worth a look: `DJ001` / `DJ008` / `DJ012` (141: 127 test models without `__str__`, 8 nullable string fields,
  6 model bodies out of Django's order), `SLOT000` / `SLOT001` (62 `str` / `tuple` subclasses without `__slots__`,
  all in tests and examples)
- [ ] 28. Security and boundaries: the `S` ratchet codes (package 16: `try`/`except: pass` 5, SQL strings 4, `assert`
  4, a weak hash, ...; `S101` is by design in tests/ and examples/ but has 19 sites elsewhere: package 4, scripts 14,
  root 1; the rest are subprocess calls, hard-coded test passwords and `pickle` in tests, examples and scripts) and
  `BLE001` (187 `except Exception` in the package, each a deliberate boundary today; turning it on means
  a `noqa` with its reason on each)
- [ ] 29. Shrink the tests/ and examples/ per-file ignores. What each code hides today:

  | Code | Hidden | Tests | Examples |
  | --- | --- | --- | --- |
  | `ANN` (`ANN201`, `ANN202`, `ANN204`, `ANN206`, `ANN205`) | 10066 | 8111 | 1955 |
  | `D` (`D103`, `D106`, `D101`, `D102`, `D205`, `D202`, ...) | 1976 | 1133 | 843 |
  | `RUF012` (mutable class default) | 1310 | 994 | 316 |
  | `ARG` | 405 | 222 | 183 |
  | `N806` | 195 | 195 | 0 |
  | `E501` | 150 | 99 | 51 |
  | `SIM117` (nested `with`) | 105 | 98 | 7 |
  | `RUF043` (`match=` metacharacters) | 94 | 91 | 3 |
  | `UP031` (printf formatting) | 48 | 0 | 48 |
  | `ERA001` | 36 | 15 | 21 |
  | `B018` | 35 | 35 | 0 |
  | `N802` | 6 | 6 | 0 |
  | `PERF` | 3 | 3 | 0 |

  scripts/ drops `PERF` (16 sites).

- [ ] 30. `ANN401` and `D107`: 34 explicit `Any` annotations and 22 undocumented `__init__`s in the package

Off by design (not planned):

- `PLC0415` (2081, import outside top level): import cycles are broken by local imports
- `TC001`-`TC003` (607): Strawberry and Django read annotations at run time, so a typing-only import would be a
  `NameError`
- `SLF001` (2559, private member access): the package shares underscore names across its modules
  (`reportPrivateUsage` is off for the same reason)
- `TID252` (917, relative imports): the package imports its siblings relatively
- `EM101`, `EM102`, `TRY003` (3097): exception-message style only
- `FBT001`-`FBT003` (306, boolean positional arguments): fixing them changes public signatures
- `PLR` complexity and magic values (`PLR2004` 1269, `PLR0913` 123, `PLR0912` 49, `PLR0911` 40, `PLR0917` 26,
  `PLR0915` 24) and `C901` (97)
- `FIX002`, `TD002`-`TD005` (35): they clash with the `TODO(spec-NNN slice N)` anchor convention (a wrapped anchor
  carries its text on the next line); the rest of `TD` and `FIX` is on
- `INP001` (69): `examples/fakeshop/tests/` is deliberately not a package, and scripts/ runs as plain
  files
- `CPY001` (511, copyright headers) and `ICN001` (38, `import datetime as dt`)
- `D203`, `D213`: the opposites of `D211` and `D212`, which the Google convention selects (ruff drops one of each
  pair)
- `D400` (1), `D401` (170, imperative mood), `D404` (6), `D413` (71): outside the Google convention

## Files ruff skips

None that it should check. `ruff check --show-files` lists exactly the 511 tracked Python files. The files it skips
are git-ignored scratch trees (`docs/shadow/`, cycle temp files, `.venv/`, `.claude/worktrees/`), read through
ruff's default `respect-gitignore`. `[tool.ruff.format]` excludes `*.md`: fenced Python in Markdown is verbatim example
content, so the formatter owns `.py` only. No file carries a file-level `# ruff: noqa`.

## Config ignores

Global `ignore`, in two commented blocks:

- Off by design (33): `C901`, `CPY001`, `D203`, `D213`, `D400`, `D401`, `D404`, `D413`, `EM101`, `EM102`,
  `FBT001`-`FBT003`, `FIX002`, `ICN001`, `INP001`, `PLC0415`, `PLR0911`, `PLR0912`, `PLR0913`, `PLR0915`, `PLR0917`,
  `PLR2004`, `SLF001`, `TC001`-`TC003`, `TD002`-`TD005`, `TID252`, `TRY003`
- Ratchet (74): the codes of items 26-28 and 30 (`ANN401`, `BLE001`, `D107`, `DJ*`, `DTZ*`, `EXE001`, `FURB*`,
  `PIE*`, `PLC*`, `PLR*`, `PLW*`, `PT*`, `PTH*`, `PYI*`, `RET*`, `S*`, `SLOT*`, `TRY300`, `TRY301`)

Per-file ignores:

| Glob | Codes |
| --- | --- |
| `tests/**/*.py` | `D`, `ANN`, `ERA001`, `SIM117`, `E501`, `N802`, `N806`, `B018`, `RUF012`, `PERF`, `RUF043`, `ARG`, `S101` |
| `examples/**/*.py` | `D`, `ANN`, `ERA001`, `SIM117`, `E501`, `UP031`, `RUF012`, `RUF043`, `ARG`, `S101` |
| `scripts/**/*.py` | `PERF`, `T201` |
| `line_count.py`, `docs/dry/export_dry_review.py` | `T201` |

## `# noqa` breakdown

Lines carrying `# noqa`: 160 (160 code hits, none bare) in 52 files: package 87, examples 50, tests 22, root 1.

| Code | Hits | Package | Tests | Examples | Root | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `A002` | 65 | 17 | 2 | 46 | 0 | an `id` parameter, the GraphQL argument name |
| `E402` | 27 | 27 | 0 | 0 | 0 | the package `__init__` creates its logger before the subpackage imports |
| `N802` | 10 | 10 | 0 | 0 | 0 | PascalCase field factories (`DjangoConnectionField`, ...), for graphene-django parity |
| `N815` | 9 | 0 | 6 | 3 | 0 | camelCase model fields the naming tests need |
| `B009` | 8 | 8 | 0 | 0 | 0 | `getattr` with a constant name, read past the stubs |
| `F821` | 7 | 0 | 7 | 0 | 0 | forward references the definition-order tests leave unresolved |
| `ARG001`, `ARG003` | 6 | 5 | 0 | 0 | 1 | framework-fixed parameters (each also carries a basedpyright suppression) |
| `N805` | 5 | 4 | 1 | 0 | 0 | metaclass methods and Django's `as_view` take `cls` |
| `N818` | 4 | 2 | 2 | 0 | 0 | control-flow exceptions, and a `DoesNotExist` mirror |
| `PERF203` | 3 | 3 | 0 | 0 | 0 | one `try` per attempt inside a loop |
| `RUF063` | 3 | 1 | 2 | 0 | 0 | reading `__annotations__` from the class `__dict__` on purpose |
| `B004`, `B010`, `B904`, `TRY004` | 8 | 8 | 0 | 0 | 0 | `__call__` probes, `setattr` past the stubs, `raise` chaining through `__context__`, `ValueError` for bad input |
| `BLE001`, `RUF012`, `F403`, `F401`, `UP006` | 5 | 2 | 2 | 1 | 0 | one each |

### Most `# noqa` per file

| File | Lines |
| --- | --- |
| `examples/fakeshop/apps/kanban/schema.py` | 23 |
| `django_strawberry_framework/__init__.py` | 18 |
| `django_strawberry_framework/middleware/debug_toolbar.py` | 10 |
| `examples/fakeshop/apps/glossary/schema.py` | 10 |
| `django_strawberry_framework/mutations/resolvers.py` | 9 |
| `tests/types/test_definition_order.py` | 8 |
| `examples/fakeshop/apps/library/schema.py` | 7 |
| `django_strawberry_framework/auth/mutations.py` | 5 |
| `django_strawberry_framework/mutations/sets.py` | 5 |
| `django_strawberry_framework/testing/client.py` | 5 |


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
