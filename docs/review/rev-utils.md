# Review: `django_strawberry_framework/utils/`

Folder pass. Sibling artifacts read: `rev-utils__relations.md`, `rev-utils__strings.md`, `rev-utils__typing.md`. Helper run on `__init__.py` (overview: zero symbols, zero markers, two local imports, one module docstring). Sibling overviews already exist under `docs/review/shadow/` from prior cycles.

## High:

None.

## Medium:

### `__init__.py` re-export contract omits the `relations` submodule

The subpackage docstring at `django_strawberry_framework/utils/__init__.py:1-12` enumerates two current submodules — `strings` and `typing` — and `__all__` re-exports `pascal_case`, `snake_case`, `unwrap_return_type`. The `relations` submodule is absent from both. However `relations` is the most-imported member of `utils/` in the package:

- `django_strawberry_framework/types/base.py:35` — `from ..utils.relations import relation_kind`
- `django_strawberry_framework/types/converters.py:28` — `from ..utils.relations import relation_kind`
- `django_strawberry_framework/types/resolvers.py:40` — `from ..utils.relations import relation_kind`
- `django_strawberry_framework/types/relations.py:9` — `from ..utils.relations import RelationKind`
- `django_strawberry_framework/optimizer/walker.py:12` — `from ..utils.relations import relation_kind`
- `tests/test_registry.py:23` — `from django_strawberry_framework.utils.relations import relation_kind`

Two issues: (1) the docstring is stale relative to on-disk contents — a new maintainer reading `utils/__init__.py` to understand the subpackage will not see `relations` listed; (2) `__all__` documents three exports but the actually-most-used pair (`relation_kind`, `RelationKind`) is reachable only via the submodule path. Per `REVIEW.md` folder-pass rule "missing package exports or too-broad exports", this is a contract gap, not a bug. Recommended change: extend the docstring bullet list to include `relations`, and either add `relation_kind` + `RelationKind` to `__all__` and the import block (preferred — every type/optimizer caller already proves these are first-class utilities) or document explicitly that relations is intentionally accessed via the submodule path. The current inconsistency between "docstring describes the contract" and "code shows the contract" matches the package-wide "documented contract not enforced" theme carried forward through worker memory.

```django_strawberry_framework/utils/__init__.py:1:17
"""Cross-cutting utility helpers.

Subpackage structure mirrors the convention both `graphene_django/utils/`
and `strawberry_django/utils/` converge on: focused submodules per
concern rather than a single 500-line `utils.py`. Currently:

- ``strings`` — case conversion (``snake_case``, ``pascal_case``).
- ``typing`` — Strawberry / Python type unwrapping (``unwrap_return_type``).
...
"""

from .strings import pascal_case, snake_case
from .typing import unwrap_return_type

__all__ = ("pascal_case", "snake_case", "unwrap_return_type")
```

### `RelationKind` `Literal` excludes a shape `tests/test_registry.py` already constructs

`django_strawberry_framework/utils/relations.py:7` defines `RelationKind` as `Literal["many", "reverse_one_to_one", "forward_single"]`. The classifier `relation_kind()` returns one of those three values. However `tests/test_registry.py:566` constructs a `PendingRelation` with `relation_kind="reverse_many_to_one"` — a fourth shape that the central classifier cannot produce and the `Literal` does not enumerate. `types/relations.py:27` types the `PendingRelation.relation_kind` field as the `RelationKind` alias, so the test value is silently outside the documented contract.

Two paths to resolution, both folder-pass material per the carry-forward note in `rev-utils__relations.md`:

1. **Extend the alias and the classifier.** Add `"reverse_many_to_one"` to the `Literal`, and teach `relation_kind()` to detect reverse FK (`auto_created` + `one_to_many`). This matches the test's intent (a reverse FK descriptor is genuinely a fourth Django relation cardinality).
2. **Fix the test value.** If the test should produce `"many"` (the current classifier's answer for `one_to_many`), update the inline construction to call `relation_kind(field)` like the other sites in the same file do (`tests/test_registry.py:273`, `:519`, `:594`).

Option 1 is the more likely correct outcome — Django's reverse FK descriptor (`ForeignRelatedObjectsDescriptor`) is conceptually distinct from a forward `ManyToMany` even though both currently collapse to `"many"` for plan-building. Either way, the package has a single source of truth for relation cardinality (this file) and the truth currently disagrees with one named test construction. Medium not Low because the `Literal` is the consumer-visible contract for a typed field stored on a registry sentinel.

```django_strawberry_framework/utils/relations.py:7
RelationKind: TypeAlias = Literal["many", "reverse_one_to_one", "forward_single"]
```

## Low:

### Utils-wide shape-guard-asymmetry stance is overdue

All three sibling artifacts (`rev-utils__relations.md` Low 1, `rev-utils__strings.md` Low 1, `rev-utils__typing.md` Low 1) flag the same pattern: the documented input contract is narrower than the parameter annotation (`field: Any`, `name: str` with implicit `camelCase`/`snake_case` precondition, `rt: Any`). `utils/relations.py` already adopted a `Protocol`-based tightening (`_RelationFieldLike` at `relations.py:10-24`); `utils/strings.py:19` and `utils/typing.py:15` did not. The folder is the right place to ratify a single stance:

- Tighten `strings.py` to `name: str` (already tight as a type but loose as a contract) — encode the strict-camelCase / strict-snake_case precondition in the docstring as the project-pass-friendly fix.
- Tighten `typing.py:15` to a `Protocol` that exposes `of_type: Any` OR rely on the `get_origin`/`get_args` path — but more importantly add a one-line docstring note that `list[T]` is assumed parameterized (Low 2 of `rev-utils__typing.md`).

The relations.py Protocol is the reference shape. This folder-pass Low replaces three per-file Lows with one folder-wide decision; defer the actual code change unless a project-pass-wide stance lands first.

### `unwrap_return_type` naming question is folder-pass material

`rev-utils__typing.md` Low 3 flags that the helper's name reads as "unwrap fully" while the docstring is explicit about one-layer semantics. The folder is the right place to ratify a single naming scheme for utils — `peel_list_one_layer` / `unwrap_list_once` surface the contract at the call site without code change beyond a rename. Two named near-future consumers (connection-field, filter argument factories per the module docstring) will inherit whichever name lands; ratify before they exist. No source change recommended this cycle; record as folder-pass naming stance.

### Module docstring's planned `queryset` submodule is a soft TODO without anchor

`django_strawberry_framework/utils/__init__.py:10-12` reads "A `queryset` submodule will land when queryset-introspection helpers become cross-cutting (currently each subsystem keeps its own)." This is exactly the kind of forward-looking note that AGENTS.md says belongs in a TODO anchor with a design-doc name — at present there is no design doc to anchor to, so the soft prose is the correct shape, but the project pass should confirm the pattern is uniform across `__init__.py` files (the optimizer/__init__.py logger declaration is the worker-memory cross-reference).

### Three `utils/` files all carry per-branch named tests under `tests/utils/`

Worth recording at the folder level as the standing test-discipline pattern for the subpackage: `tests/utils/test_relations.py`, `tests/utils/test_strings.py`, `tests/utils/test_typing.py` each pin every branch the corresponding helper documents. This is what kept "missing tests for important branches" Medium off all three per-file artifacts. Future submodules (`queryset`, when it lands) should follow the same convention — pin every documented branch in a sibling `tests/utils/test_<submodule>.py` rather than relying on incidental optimizer/types integration coverage.

## What looks solid

- Helper ran on `utils/__init__.py` as required by the folder-pass rule for `__init__.py` files (`docs/review/REVIEW.md` "Static review helper" section). Output: zero symbols, zero hotspots, zero ORM markers, zero calls of interest, zero TODO comments, zero repeated literals. The `__init__.py` is a pure re-export shim with one docstring.
- All three `utils/` submodules are stdlib-leaf: no Django, no Strawberry, no framework imports at module top. `from __future__ import annotations` consistently used. Zero import-time side effects across the folder. No circular-import risk.
- Dependency direction inside the folder is clean — no `utils/` file imports from another `utils/` file. The folder is a flat collection of leaves.
- Cross-folder import direction matches the documented layering: `types/` and `optimizer/` consume `utils/`, never the reverse. No sibling has started importing back into `utils/`.
- Repeated-literals cross-check across the three sibling overviews surfaces nothing — each file's literals are local-only (case-conversion examples, branch labels). No literal appears in two files in the folder.
- Imports cross-check across sibling overviews: `relations.py` adds `Protocol`/`runtime_checkable`/`Literal`/`TypeAlias` from `typing` (Low 1's Protocol fix); `strings.py` imports nothing beyond stdlib types implied by signatures; `typing.py` imports `Any`/`get_args`/`get_origin` from `typing` — the three files form a deliberately thin surface.
- The two existing `__all__` entries map exactly to the two listed submodules in the docstring; the inconsistency is only that a third submodule (`relations`) exists on disk and is not represented in either.
- The folder is the right home for these helpers per AGENTS.md "reusable utilities only when genuinely shared" — each utility has ≥2 first-party callers, and `relation_kind` has 5.

---

### Summary:

Three small stdlib-leaf modules with clean dependency direction, no import-time side effects, and per-branch named test coverage. The folder-level findings are structural rather than logic. Two Mediums: (1) the `__init__.py` re-export contract is stale — `relations` is the most-imported submodule but is absent from both the docstring and `__all__`, recommend extending both; (2) `RelationKind` `Literal` excludes `"reverse_many_to_one"` that `tests/test_registry.py:566` already constructs against the typed `PendingRelation.relation_kind` field — either extend the alias + classifier (preferred) or fix the test. Four Lows are folder-pass-ratification material: the shape-guard-asymmetry stance (relations.py already moved to `Protocol`, strings/typing did not), the `unwrap_return_type` naming question, the soft `queryset` future-submodule prose in the `__init__.py` docstring, and the standing `tests/utils/test_<submodule>.py` per-branch convention.

Cross-folder carry-forward to the project pass: (a) shape-guard-asymmetry pattern now spans 6 files (field_meta, converters, resolvers, relations, strings, typing) per worker memory — package-wide stance overdue; (b) `__init__.py` re-export contract inconsistencies are worth confirming uniformly across `optimizer/__init__.py`, `types/__init__.py`, and the top-level package `__init__.py`; (c) the `__init__.py` docstring "Currently:" enumeration pattern should be ratified as the standing convention for subpackage entry points or dropped uniformly.

## Verification

PASS. Worker 2 addressed both Mediums per the artifact's preferred option:

- Medium 1 (`__init__.py` re-export contract): docstring now lists `relations` alongside `strings` and `typing`; `__all__` and the import block add `RelationKind` and `relation_kind`. Matches the preferred-path recommendation exactly.
- Medium 2 (`RelationKind` missing `"reverse_many_to_one"`): `Literal` extended to four shapes and `relation_kind()` taught to detect reverse FK via `auto_created=True` + `one_to_many=True`. Forward M2M short-circuit reordered so it never falls through to the reverse-FK probe. Docstring documents all four shapes. The `tests/test_registry.py:566` construction is now inside the contract.
- Bonus: `field: Any` annotation tightened to `_RelationFieldLike` Protocol (`@runtime_checkable`, four bool flags) — this is the folder-pass shape-guard-asymmetry Low partially landing for relations.py; the `getattr(..., False)` runtime guard is retained.

Validation:

- `uv run pytest tests/utils tests/test_registry.py tests/types -q --no-cov` → 131 passed, 1 skipped. The four `RelationKind`/`relation_kind` direct call sites in `tests/utils/test_relations.py` exercise the new `"reverse_many_to_one"` branch (per the diff stat `tests/utils/test_relations.py | 33 ++-` and the artifact's pinned-branches convention).
- `uv run pytest tests/ -q --no-cov` → 378 passed, 6 failed. The six failures are all `ImportError: cannot import name '_will_lazy_load'` in `tests/optimizer/test_extension.py` and originate from the `types/resolvers.py` cycle (the helper was split into `_will_lazy_load_single`/`_will_lazy_load_many` and the replacement tests live in `tests/types/test_resolvers.py`). The orphan imports in `tests/optimizer/test_extension.py:1199-1255` are out-of-scope for the `utils/` folder pass and predate this cycle's diff. Flagging as a follow-up for the `types/resolvers.py` cycle / optimizer-folder retrospective rather than blocking this folder pass.

Checklist item `docs/review/review-0_0_4.md` folder pass for `utils/` marked complete.
