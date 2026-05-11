# Review: `django_strawberry_framework/utils/strings.py`

## High:

None.

## Medium:

None.

## Low:

### `snake_case` silently mangles non-strict camelCase inputs

The docstring warns that an acronym input like `"HTMLParser"` becomes `"h_t_m_l_parser"` and notes the case is unreachable through Strawberry's documented call chain. That is fine for the current single caller, but the function takes `name: str` with no guard and is exported as a utility, so a future direct caller passing an already-`snake_case` name with a stray capital, or a `PascalCase` type name, gets silent corruption rather than a no-op or an error. Two reasonable options: tighten the docstring to "strict lowerCamelCase only; behavior on other inputs is unspecified", or short-circuit when the input already contains an underscore (matches how `pascal_case` tolerates non-strict input by collapsing underscores). No change required for the current call site; flagging at Low for the folder/project pass to decide whether utility-level input contracts should be uniform across `utils/`.

```django_strawberry_framework/utils/strings.py:19:43
def snake_case(name: str) -> str:
    ...
    for i, c in enumerate(name):
        if i > 0 and c.isupper():
            out.append("_")
        out.append(c.lower())
```

### `pascal_case` empty-string and all-underscore inputs return `""`

`pascal_case("")` and `pascal_case("___")` both return `""` because the `if part` filter drops every empty split. That is almost certainly the right behavior (it preserves the "underscores collapse to nothing" contract documented in the docstring) but it is undocumented and the empty-return case is not covered by `tests/utils/test_strings.py`. Symptom would be a downstream `<TypeName><FieldName>Enum` name like `<TypeName>Enum` when a field name is malformed. Low because (a) the converter's call site derives `name` from `field.name`, which Django guarantees is non-empty and a valid identifier, and (b) the existing tests pin every realistic shape. Either add a one-line test pinning the empty/underscore-only return, or document the contract; do not add a guard — Django shields the only caller.

```django_strawberry_framework/utils/strings.py:46:60
def pascal_case(name: str) -> str:
    ...
    return "".join(part.capitalize() for part in name.split("_") if part)
```

### `str.capitalize()` lowercases the tail of each segment

`"".capitalize() == ""`, `"ID".capitalize() == "Id"`, `"iPhone".capitalize() == "Iphone"`. For Django `snake_case` field names this is correct (segments are already lowercase). Worth a single line in the docstring noting that segments are assumed lowercase, mirroring the explicit "strict camelCase only" caveat on `snake_case`. Same calibration as the prior two items — utility-level input contract clarity, deferred to the folder pass.

```django_strawberry_framework/utils/strings.py:60:60
    return "".join(part.capitalize() for part in name.split("_") if part)
```

## What looks solid

- Module is a pure stdlib leaf with no Django, Strawberry, or framework imports; zero import-time side effects; no circular-import risk.
- Both functions have docstrings that name the call site (optimizer name lookup; choice-to-enum schema name) and document the exact `Strawberry camelCase` <-> `Django snake_case` boundary they bridge — matches the AGENTS.md "Two Scoops" preference for utilities placed where future maintainers expect them.
- `pascal_case`'s underscore-collapsing contract is exercised by `tests/utils/test_strings.py` for leading / trailing / double-underscore inputs; `snake_case`'s three documented examples all have matching assertions.
- Static helper skipped: 61-line stdlib-leaf utility outside `optimizer/` and `types/`; helper is not mandatory under the REVIEW.md "when to run" rules. Per-branch coverage is already pinned by `tests/utils/test_strings.py`.
- Module docstring's "if a third style ever shows up we'll add it here" rule matches the standing AGENTS.md "do not preemptively add" stance — kept minimal on purpose.

---

### Summary:

A 61-line stdlib-leaf utility with two case-conversion helpers, each with a single documented caller (optimizer name lookup; choice-to-enum schema name generation). Logic is correct for every shape the documented call chain produces, and per-branch tests in `tests/utils/test_strings.py` pin the realistic inputs. The three Low findings are all utility-level input-contract clarifications (`snake_case` acronym handling, `pascal_case` empty/all-underscore return, `capitalize()` tail-lowercasing assumption) and should be settled at the `utils/` folder pass alongside `utils/relations.py`'s same-shape `field: Any` looser-than-documented contract Low, not fixed per-file. No High or Medium concerns; no test gaps for documented behavior.

## Verification

PASS — no-source-change cycle. Zero High/Medium; all three Lows explicitly framed in artifact body as utility-level input-contract clarifications deferred to the `utils/` folder pass (paired with `utils/relations.py` Low 2). No diff to `django_strawberry_framework/utils/strings.py` or `tests/utils/test_strings.py`. `uv run pytest tests/utils -q --no-cov` → 9 passed.
