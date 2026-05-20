# Review: `django_strawberry_framework/utils/strings.py`

Status: verified

## DRY analysis

- None — `utils/strings.py` is a pure-stdlib leaf module with two short case-conversion helpers; the docstring already names the only deferred extension condition ("a third style would land here").

## High:

None.

## Medium:

None.

## Low:

### `pascal_case` silently lower-cases interior upper characters

`pascal_case` is defined as `snake_case → PascalCase`, and every documented call site (the choice-to-enum builder at `types/converters.py:289` feeding a Django `field.name`) supplies a strict `snake_case` Django identifier where every character is already lowercase. The implementation, however, uses `str.capitalize()` per segment, which lowercases interior characters: `pascal_case("my_HTTP_response")` returns `"MyHttpResponse"`, not `"MyHTTPResponse"`. This is unreachable through the documented call chain (Django field names cannot contain uppercase) but parallels the existing "strict camelCase only — acronyms are not handled" caveat that `snake_case` already documents at `django_strawberry_framework/utils/strings.py:26-31`. Add an analogous one-paragraph caveat under the `pascal_case` docstring so a future direct caller is not surprised by the lower-case-the-tail behavior. No code change.

```django_strawberry_framework/utils/strings.py:46:60
def pascal_case(name: str) -> str:
    """Convert a ``snake_case`` Django field name to ``PascalCase``.

    Adjacent / leading / trailing underscores collapse to nothing, which
    keeps generated GraphQL type names stable when consumers use names
    like ``_legacy_id`` or ``status_``.
    ...
    """
    return "".join(part.capitalize() for part in name.split("_") if part)
```

### `snake_case` empty-string and `pascal_case` all-underscore inputs are not pinned by tests

`snake_case("")` returns `""` (zero loop iterations) and `pascal_case("_")` / `pascal_case("__")` returns `""` (every segment filtered out by `if part`). Both are documented-by-implementation but not test-pinned; the closest coverage at `tests/utils/test_strings.py:17-19` exercises `"_leading"`, `"trailing_"`, and `"double__underscore"` (each still produces at least one non-empty segment). The empty-output behavior is unreachable through the documented call chain (Django field names are never empty and never `"_"`), but a one-line test pinning `pascal_case("") == ""` and `pascal_case("_") == ""` would make the silent-empty contract explicit and prevent a future regression — e.g., a maintainer "fixing" the filter to keep empty segments would silently change enum names. Same shape as the `tests/utils/test_relations.py:21-24` unreachable-branch pin that the `utils/relations.py` review (worker-memory) cited as the right idiom.

```django_strawberry_framework/utils/strings.py:60:60
    return "".join(part.capitalize() for part in name.split("_") if part)
```

### Docstring example block format mixes prose-and-code

Both function docstrings end with an `Examples:` block where each pair sits on its own line followed by a `;` — e.g. `"name"` -> `"name"`; on `django_strawberry_framework/utils/strings.py:34-36` and `:54-58`. The trailing `;` reads as a sentence separator but the entries are individually parseable lines. Sibling `utils/relations.py` docstrings (per the prior cycle's review) use a simpler bullet-style. Strictly cosmetic — flagging because the maintainer's `worker-memory/worker-1.md` cross-cycle calibration noted that "docstring example format" consistency at the folder pass is worth a unified pass when we get there, not a per-file rewrite now.

```django_strawberry_framework/utils/strings.py:33:37
    Examples:
        ``"name"`` -> ``"name"``;
        ``"isPrivate"`` -> ``"is_private"``;
        ``"createdDate"`` -> ``"created_date"``.
    """
```

## What looks solid

### DRY recap

- **Existing patterns reused.** Both helpers are pure-stdlib (`str.isupper`, `str.lower`, `str.split`, `str.capitalize`, list-join) and import nothing — no `re`, no project-internal call. They are the canonical owners of case conversion in the package, exactly as the module docstring at `django_strawberry_framework/utils/strings.py:1-16` promises. Consumer call sites are exhaustive and route through this module: `snake_case` at `django_strawberry_framework/optimizer/walker.py:175,540,677`, `django_strawberry_framework/types/base.py:168,792`, and `django_strawberry_framework/types/finalizer.py:192`; `pascal_case` at `django_strawberry_framework/types/converters.py:289` for the `f"{type_name}{pascal_case(field.name)}Enum"` schema-name builder. Re-export through `django_strawberry_framework/utils/__init__.py:18,24,26` is consistent with the sibling `utils/relations.py:1-70` shape. Tests pin both functions at `tests/utils/test_strings.py:6-19` and indirectly through `tests/types/test_relay_interfaces.py:45`, `tests/optimizer/test_walker.py:99,1638,1689`.
- **New helpers a fix might justify.** None. The "third style would land here" comment at `django_strawberry_framework/utils/strings.py:13-15` is the explicit charter; no current carry-forward names a third case-style. The `{snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}` dict-comp repeats verbatim at `types/base.py:168`, `tests/types/test_relay_interfaces.py:45`, `tests/optimizer/test_walker.py:99,1638,1689` — this is the `field_map` construction contract (a per-cycle carry-forward from `worker-memory/worker-1.md`'s project-pass to-do list), not a strings-module concern. The shape is correctly load-bearing at the `definition.field_map` boundary; do **not** push it down into a `utils/strings.py` helper.
- **Duplication risk in the current file.** None. Static helper's repeated-literal report at `docs/shadow/django_strawberry_framework__utils__strings.overview.md:39-41` returned "None." Both functions are ~5 lines and share no copy-pasted branch logic; they are inverse-direction siblings only at the *concept* level (snake↔pascal), not at the implementation level.

### Other positives

- Single-source ownership of `snake_case` and `pascal_case` for the whole package. The module docstring at `django_strawberry_framework/utils/strings.py:1-16` explicitly pins this charter, and a package-wide `grep` confirms no `re.sub(...)` or `.capitalize()` re-derivation lives anywhere else (only the two implementations here). The carry-forward from `rev-types__base.md` and `rev-types__converters.md` — that `snake_case` is the field_map key contract and `pascal_case` is the enum-name builder — is satisfied at exactly one call site each per consumer.
- `snake_case` already documents its known edge case (`"HTMLParser" → "h_t_m_l_parser"`) and explains it is unreachable through the Strawberry call chain. This is the right shape for a low-risk helper: the unreachable branch is documented, not defended.
- `pascal_case` correctly filters empty segments via `if part`, which keeps `_leading`, `trailing_`, and `double__underscore` producing stable PascalCase names. Test pins at `tests/utils/test_strings.py:17-19` cover the three collapse cases.
- Zero imports, zero side effects, zero ORM markers (the helper's `Django / ORM markers` table at `docs/shadow/django_strawberry_framework__utils__strings.overview.md:22-24` only matches the literal word "only" inside the docstring at `:26`, a false positive). Pure-function module is safe to import at any phase.
- Repeated-string-literal report from the static helper is `None.` — there is genuinely no within-file duplication to consolidate.

### Summary

`utils/strings.py` is a canonical leaf module of the same shape as `utils/relations.py`: pure-stdlib, single-source ownership of both case-conversion helpers consumed across `optimizer/walker.py`, `types/base.py`, `types/finalizer.py`, and `types/converters.py`. The carry-forward from `rev-types__base.md` (snake_case feeds the `field_map` key contract) and `rev-types__converters.md` (pascal_case feeds the enum-name builder) confirms the helpers are wired to exactly one canonical consumer each per direction. No High or Medium findings; three Low items propose docstring polish on `pascal_case`'s lower-cases-interior-uppercase behavior (mirroring `snake_case`'s existing acronym caveat), a one-line test pin for the empty-string / all-underscore inputs, and a flag for unified docstring-example formatting at the upcoming folder pass.

---

## Fix report (Worker 2)

Consolidated single-pass cycle (logic + comment + changelog disposition) per
the dispatch brief — 0H/0M/3L with the only in-cycle edits being the L1
docstring caveat and the L2 test pins. L3 (folder-pass docstring example
formatting) is explicitly deferred to the upcoming `utils/` folder pass.

### Files touched

- `django_strawberry_framework/utils/strings.py` — **L1**: added an acronym
  caveat paragraph under `pascal_case`'s docstring mirroring `snake_case`'s
  existing caveat, noting that per-segment `str.capitalize()` lower-cases
  interior upper-case characters (so `"my_HTTP_response"` becomes
  `"MyHttpResponse"` rather than `"MyHTTPResponse"`). Behavior-preserving
  docstring polish; no code change.
- `tests/utils/test_strings.py` — **L2**: added `test_pascal_case_empty_output_edges`
  pinning `pascal_case("") == ""` and `pascal_case("_") == ""`. Verified
  current behavior by reading the implementation: `"".split("_")` yields
  `[""]` and `"_".split("_")` yields `["", ""]`, both filtered out by
  `if part`, joining to `""`.

### Tests added or updated

- `tests/utils/test_strings.py::test_pascal_case_empty_output_edges` — pins
  the silent-empty contract for both inputs, matching the
  `tests/utils/test_relations.py:21-24` unreachable-branch idiom Worker 1
  cited.

### Validation run

- `uv run ruff format .` — pass, 101 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed.
- `uv run pytest tests/utils/ -x` — 16 passed (focused). Coverage gate
  failure is the expected by-product of running a focused subset against
  a 100%-fail-under config; `utils/strings.py` itself is at 100% in the
  focused run.

### Notes for Worker 3

- **L3 deferred to folder pass.** Worker 1's L3 ("docstring example block
  format mixes prose-and-code") is explicitly framed as a unified pass at
  the upcoming `utils/` folder pass, citing the maintainer's cross-cycle
  calibration: "docstring example format consistency at the folder pass
  is worth a unified pass when we get there, not a per-file rewrite now."
  Quoted verbatim per the worker-2 memory pattern for carry-forward
  audit-trail discipline.
- **L1 mirrors the existing caveat shape** at `utils/strings.py:26-31` —
  same "Strict ... only — acronyms are *not* handled" framing, same
  "unreachable through the documented call chain ... documented here so
  a future direct caller is not surprised" closer. Behavior-preserving.
- **L2 pin uses inline comment** explaining the silent-empty contract and
  why pinning it matters (a future filter "fix" would silently change
  generated enum names). No source change; both inputs return the
  documented-by-implementation empty string today.

---

## Verification (Worker 3)

### Logic verification outcome

- **L1 (`pascal_case` acronym caveat)** — applied. The new ten-line paragraph at `django_strawberry_framework/utils/strings.py:53-61` mirrors `snake_case`'s acronym caveat shape verbatim ("Strict ... only — acronyms ... *not* ... documented here so a future direct caller is not surprised") and correctly names the lower-cases-interior behavior with the cited example (`"my_HTTP_response"` → `"MyHttpResponse"`). Behavior-preserving docstring polish; the implementation at `:70` is unchanged. Verified.
- **L2 (empty-string and all-underscore test pin)** — applied. `tests/utils/test_strings.py::test_pascal_case_empty_output_edges` at `tests/utils/test_strings.py:22-29` pins both `pascal_case("") == ""` and `pascal_case("_") == ""`, with an inline comment matching Worker 1's framing ("a future filter 'fix' would silently change generated enum names"). Test passes in the focused run; the silent-empty contract is now grep-discoverable.
- **L3 (Examples-block format)** — intentionally deferred to the upcoming `utils/` folder pass per Worker 1's own prose ("worth a unified pass when we get there, not a per-file rewrite now") and quoted verbatim in Worker 2's notes. Acceptable deferral; the trigger condition (folder pass) is named.

### DRY findings disposition

DRY analysis returned "none" across all three sub-items (existing patterns, new helpers, current-file duplication). No DRY-driven edits were warranted; the L1 caveat addition follows the existing `snake_case` caveat shape verbatim, which is itself the DRY-correct path (parallel sibling docstrings, not divergent ones). Verified.

### Temp test verification

No temp tests created. The L2 permanent test pin (`test_pascal_case_empty_output_edges`) is sufficient proof for the silent-empty contract; the cycle's scope is too small to warrant additional temp-test confirmation.

### Verification outcome

`cycle accepted; verified`

- `git diff -- CHANGELOG.md` empty — confirms changelog disposition "not warranted" was honored (no edit). Dual citation (AGENTS.md ban + active plan's lack of authorization + no public-API/observable-behavior change) is correctly present in the artifact at the `## Changelog disposition` section.
- `git diff -- django_strawberry_framework/utils/strings.py tests/utils/` confined to (a) the ten-line L1 docstring caveat at `utils/strings.py:53-62` and (b) the eight-line L2 test pin at `tests/utils/test_strings.py:21-28`. No fresh edits snuck in.
- `uv run pytest tests/utils/ -x` — 16 passed; `utils/strings.py` itself at 100% in focused coverage. Total-coverage 29% failure is the expected focused-subset artifact, not a regression.
- L1+L2 applied in-cycle; L3 explicitly deferred to the folder pass with trigger condition named. Cycle is terminal.

---

## Comment/docstring pass

Folded into the consolidated single pass above. The L1 acronym-caveat
addition to `pascal_case`'s docstring is the entire comment-pass surface
for this cycle; it describes the final approved behavior (per-segment
`str.capitalize()` lower-cases interior upper-case characters) and
mirrors the analogous caveat already on `snake_case`. No other comments
or docstrings on the file required edits — the module docstring at
`utils/strings.py:1-16` already documents the charter, and `snake_case`'s
docstring is unchanged.

L3 (Examples-block format unification across the `utils/` folder) is
**deferred** to the upcoming `utils/` folder pass per Worker 1's own
framing and the cross-cycle calibration captured in worker-memory; no
per-file rewrite is appropriate here.

---

## Changelog disposition

**Not warranted.** Cycle changes are an internal docstring caveat
(`pascal_case` now documents an unreachable-through-the-documented-call-chain
acronym behavior) and a test pin for an unreachable empty-output edge —
neither is consumer-visible. `AGENTS.md` "Do not update CHANGELOG.md
unless explicitly instructed" + active-plan silence + no public-symbol
change + no observable behavior change = straight "not warranted" per the
worker-memory pattern for docstring-polish-plus-test-pin cycles. No edit
to `CHANGELOG.md`.

---

## Iteration log

_Append-only — Worker 2 / Worker 3 re-passes attach here._
