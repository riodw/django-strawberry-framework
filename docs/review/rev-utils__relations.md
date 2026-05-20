# Review: `django_strawberry_framework/utils/relations.py`

Status: verified

## DRY analysis

- **Existing patterns reused.** This module is the canonical leaf — it is reused by, not reusing. `RelationKind` (`utils/relations.py:7-12`), `relation_kind` (`utils/relations.py:39-65`), `is_many_side_relation_kind` (`utils/relations.py:68-70`), and `MANY_SIDE_RELATION_KINDS` (`utils/relations.py:14-19`) are read by `optimizer/field_meta.py:26-29,104-111,156`, `optimizer/walker.py:14,74,441-442,605`, `types/resolvers.py:46,144,196`, and `types/relations.py:24,53`. Internally, `is_many_side_relation_kind` reuses the canonical `MANY_SIDE_RELATION_KINDS` frozenset (`utils/relations.py:14-19,70`). `relation_kind` uses defensive `getattr(..., False)` on the four `_RelationFieldLike` flags (`utils/relations.py:57-63`); this is the same defensive-default pattern `FieldMeta.from_django_field` uses (`optimizer/field_meta.py:113-170`) so descriptor-shape variations don't trip the classifier. The package public surface (`utils/__init__.py:17,22-25`) re-exports the three symbols and they are pinned at `tests/utils/test_relations.py:46-50` to be identity-equal to the submodule originals.
- **New helpers a fix might justify.** None. The module is the right home for the responsibility (Django-relation-shape classification) and its three symbols are correctly factored: a `Literal` alias enumerating the four kinds, a frozenset enumerating the many-side subset, a classifier that reads four boolean flags, and a membership helper. There is no further extraction worth doing. The previous review cycle (`rev-optimizer__field_meta.md` M1/L2) already consolidated `FieldMeta.relation_kind` / `FieldMeta.is_many_side` to delegate here, so the canonical seam is in place.
- **Duplication risk in the current file.** Minor. The four string literals `"many"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"` each appear twice — once in the `Literal` alias (`utils/relations.py:8-11`), once in the classifier `return` (`utils/relations.py:58,61,64,65`); the helper's repeated-literal report flags `reverse_many_to_one` (3x — alias, classifier, plus `MANY_SIDE_RELATION_KINDS` at line 17), `reverse_one_to_one` (2x), `forward_single` (2x), and `auto_created` (2x). The alias-vs-return pairs are structural — Python `Literal[...]` does not allow referencing a single source-of-truth identifier — so the duplication is unavoidable given the closed-set typing shape. The `auto_created` repetition at lines 60 and 63 is two distinct `getattr` reads against the same flag, also structural (one inside the `one_to_many` branch, one for the `one_to_one + auto_created` reverse-O2O check). No cross-file duplication risk: the canonical `MANY_SIDE_RELATION_KINDS` frozenset is the single source of truth for the many-side rule, and the consolidations performed in the prior cycle (`rev-optimizer__field_meta.md` M1) eliminated the only known external copy of `{"many", "reverse_many_to_one"}`.

## High:

None.

## Medium:

None.

## Low:

### `_RelationFieldLike` is `@runtime_checkable` with no `isinstance` call sites

`_RelationFieldLike` at `utils/relations.py:22-36` is decorated `@runtime_checkable`, but a package-wide grep finds zero `isinstance(..., _RelationFieldLike)` call sites — every consumer threads the four-flag shape through static typing only. This is the same "Protocol decorated runtime_checkable with no isinstance consumer" pattern the prior cycle removed from `optimizer/field_meta._DjangoFieldLike` (per `rev-optimizer__field_meta.md`'s L3 fix). `@runtime_checkable` carries non-trivial cost: it forces `_ProtocolMeta.__instancecheck__` to walk attribute existence at runtime if anyone ever does invoke `isinstance` against it, and it advertises a runtime contract the module does not actually rely on. Dropping the decorator and the `runtime_checkable` import keeps the structural-typing contract intact (every caller already passes a real Django relation field; `mypy`/`pyright` enforce the four-flag protocol statically) and matches the convention established by the `_DjangoFieldLike` fix.

```django_strawberry_framework/utils/relations.py:5:36
from typing import Literal, Protocol, TypeAlias, runtime_checkable
...
@runtime_checkable
class _RelationFieldLike(Protocol):
    """Shape contract for the four Django relation flags this classifier reads."""

    many_to_many: bool
    one_to_many: bool
    one_to_one: bool
    auto_created: bool
```

### Docstring repeated-literal hint — `forward_single` description could name `OneToOneField` once

`relation_kind`'s docstring at `utils/relations.py:53-55` describes `"forward_single"` as "every other forward single-row relation (`ForeignKey`, forward `OneToOneField`)". That phrasing is correct, but `"reverse_one_to_one"` at lines 52-53 says "the reverse side of a `OneToOneField` (`one_to_one=True` + `auto_created=True`)" — so the docstring uses `OneToOneField` twice, once for the reverse side and once as part of the forward-single catchall. The current shape is fine; flagging only as a low-tier maintainability note: when this docstring is next polished, consider tightening so a maintainer reading "forward_single" sees the explicit "forward-side" framing (`ForeignKey`, forward `OneToOneField` — i.e., `auto_created=False`) without having to cross-reference the reverse-side branch above. Not a logic concern; defer to comment-pass discretion.

```django_strawberry_framework/utils/relations.py:42:56
Four shapes are distinguished:

- ``"many"`` — forward ``ManyToManyField`` (``many_to_many=True``).
- ``"reverse_many_to_one"`` — the reverse side of a ``ForeignKey``
  (Django's ``ManyToOneRel`` descriptor: ``one_to_many=True`` paired
  with ``auto_created=True``). Cardinality-wise this collapses into
  the many-side for plan building today, but the descriptor itself
  is conceptually distinct from a forward M2M and is named so
  consumers (and the registry's typed ``PendingRelation`` sentinel)
  can disambiguate.
- ``"reverse_one_to_one"`` — the reverse side of a
  ``OneToOneField`` (``one_to_one=True`` + ``auto_created=True``).
- ``"forward_single"`` — every other forward single-row relation
  (``ForeignKey``, forward ``OneToOneField``).
```

### Classifier's `one_to_many=True, auto_created=False` branch returns `"many"` — structurally unreachable for real Django shapes

`relation_kind` at `utils/relations.py:59-62` handles the case where `one_to_many=True` and `auto_created=False` by returning `"many"`. Django's `ManyToOneRel` (the only descriptor that sets `one_to_many=True`) is always `auto_created=True` because reverse relations are synthesized by Django at model-meta-build time. The `return "many"` at line 62 therefore covers a shape that no real Django descriptor produces. The branch is test-pinned at `tests/utils/test_relations.py:21-24` with a `SimpleNamespace(one_to_many=True, auto_created=False)` constructed by hand — so the contract is preserved for shape-permissive callers and `mypy` does not have to prove unreachability — but a future reader may wonder why the inner `auto_created` check has a fall-through at all. Two options if ever revisited: (a) collapse the branch to `if one_to_many and auto_created: return "reverse_many_to_one"` with a falling-through `return "forward_single"` at the bottom (simpler, but changes the contract for the synthetic test shape); (b) leave the branch and add a one-line docstring sentence stating "the `one_to_many=True, auto_created=False` shape is not produced by Django but is classified as the many-side for caller-flexibility, since `one_to_many` alone already encodes list cardinality". Defer; the current shape is conservative and the test pins it.

```django_strawberry_framework/utils/relations.py:57:65
if getattr(field, "many_to_many", False):
    return "many"
if getattr(field, "one_to_many", False):
    if getattr(field, "auto_created", False):
        return "reverse_many_to_one"
    return "many"
if getattr(field, "one_to_one", False) and getattr(field, "auto_created", False):
    return "reverse_one_to_one"
return "forward_single"
```

### `is_many_side_relation_kind` typed as `kind: object` while real call sites pass `RelationKind | None`

`is_many_side_relation_kind` at `utils/relations.py:68-70` annotates `kind: object`. Real call sites pass: a `RelationKind` value from `FieldMeta.relation_kind` (`optimizer/field_meta.py:111`), a `RelationKind` value from `field_meta.relation_kind` (`types/resolvers.py:144`), and an `object` (test cases passing `None` at `tests/utils/test_relations.py:58`). The wider `object` annotation is intentional — it lets `kind in MANY_SIDE_RELATION_KINDS` accept arbitrary inputs without `mypy` complaining about narrowing — but it also hides the contract from readers who'd expect `RelationKind | None`. A tightened annotation `kind: RelationKind | None` (or `kind: RelationKind | object` if `None` is just one of many tolerated junk values) would make the test-tolerance contract explicit. Low-tier polish; the runtime semantic is unchanged because `in frozenset(...)` is total over hashables and falsy for non-members.

```django_strawberry_framework/utils/relations.py:68:70
def is_many_side_relation_kind(kind: object) -> bool:
    """Return ``True`` for relation kinds represented as GraphQL lists."""
    return kind in MANY_SIDE_RELATION_KINDS
```

## What looks solid

- **Single source of truth for the many-side rule.** `MANY_SIDE_RELATION_KINDS` at `utils/relations.py:14-19` is the canonical frozenset. The prior cycle (`rev-optimizer__field_meta.md` M1) consolidated the only known external copy of `{"many", "reverse_many_to_one"}` to call `is_many_side_relation_kind` instead, so this module is now the single read seam for "is this kind list-valued in GraphQL?".
- **Defensive `getattr(..., False)` reads.** `relation_kind` at `utils/relations.py:57-63` reads each flag with `getattr(field, "<flag>", False)`, matching the docstring's "the narrower annotation documents the read contract; `getattr(..., False)` in the body still defends against shapes that omit a flag." This belt-and-suspenders pattern is consistent with `FieldMeta.from_django_field` (`optimizer/field_meta.py:113-170`).
- **`Literal` alias as a closed set.** `RelationKind` at `utils/relations.py:7-12` is a closed `Literal`, so `mypy`/`pyright` enforce exhaustiveness at every call site that narrows on the kind value (e.g., `kind == "reverse_one_to_one"` at `types/resolvers.py:196`, `optimizer/field_meta.py:156`).
- **Frozen immutable many-side set.** `frozenset(...)` at `utils/relations.py:14-19` is module-load-time-constructed, immutable, and reused by reference everywhere `is_many_side_relation_kind` is called — no per-call allocation, no mutation surface.
- **Identity re-export contract pinned.** `tests/utils/test_relations.py:46-50` asserts `utils.relation_kind is utils.relations.relation_kind`, `utils.RelationKind is utils.relations.RelationKind`, and `utils.is_many_side_relation_kind is utils.relations.is_many_side_relation_kind`. The package-public-surface contract is tested as identity-equal to the submodule originals, so a maintainer accidentally re-implementing instead of re-exporting would break the test surface.
- **Test surface covers all four `RelationKind` arms.** `tests/utils/test_relations.py:15-70` pins `"many"` (forward M2M), `"many"` (one_to_many fall-through), `"reverse_many_to_one"` (auto_created + one_to_many), `"reverse_one_to_one"` (auto_created + one_to_one), and `"forward_single"` (one_to_one without auto_created). Plus `is_many_side_relation_kind` is pinned across `"many"` / `"reverse_many_to_one"` / `"reverse_one_to_one"` / `"forward_single"` / `None` (`tests/utils/test_relations.py:53-58`).
- **No Django ORM markers, no control-flow hotspots.** The static helper overview at `docs/shadow/django_strawberry_framework__utils__relations.overview.md` reports zero `_meta` / `QuerySet` / `Prefetch` / `_prefetched_objects_cache` / `fields_cache` references and zero functions over the 40-line / 8-branch hotspot threshold. The module is a pure logical leaf — no ORM side effects, no import-time work beyond defining the alias / frozenset / class / two functions, no circular-import risk (only standard-library imports).
- **Helper ran cleanly despite being optional.** Per `worker-1.md`, the helper is only mandatory under `optimizer/` and `types/`; `utils/` is opt-in. Ran anyway because the file is the canonical leaf module cited across the package. Overview confirms zero unexpected markers.

### Summary

`utils/relations.py` is the 70-line canonical leaf module for the package's relation-kind classification. It correctly factors the responsibility into a `Literal` alias, a `frozenset` of the many-side subset, a defensive four-flag classifier, and a membership helper — all consumed by `optimizer/field_meta.py`, `optimizer/walker.py`, `types/resolvers.py`, and `types/relations.py`. 0 High / 0 Medium / 4 Low findings. The four Lows are: (L1) `@runtime_checkable` on `_RelationFieldLike` with no `isinstance` call sites, matching the `_DjangoFieldLike` shape the prior cycle removed; (L2) docstring polish hint for the `"forward_single"` branch description; (L3) the `one_to_many=True, auto_created=False → "many"` branch is structurally unreachable for real Django shapes but test-pinned for shape-permissive callers, worth a docstring sentence if ever revisited; (L4) `is_many_side_relation_kind(kind: object)` is wider than the real call-site contract `RelationKind | None`. No DRY duplication, no logic bugs, single source of truth for the many-side rule already established by the prior cycle's consolidation. The module is the reference shape for a small leaf utility module in this package.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/utils/relations.py` — applied L1 (dropped `@runtime_checkable` decorator on `_RelationFieldLike` and the `runtime_checkable` import, mirroring the prior `_DjangoFieldLike` fix in `optimizer/field_meta.py`) and L4 (tightened `is_many_side_relation_kind`'s `kind: object` annotation to `kind: RelationKind | None` matching the real call-site contract).

### Tests added or updated

- None. L1 is a pure decorator/import removal with no behavior change; the existing test surface (`tests/utils/test_relations.py`) already exercises every classifier branch and the `is_many_side_relation_kind` contract including the `None` case. L4 tightens the annotation to exactly what the existing test at `tests/utils/test_relations.py:58` passes (`None`), so no new test is needed.

### Validation run

- `uv run ruff format .` — pass (no changes).
- `uv run ruff check --fix .` — pass (all checks).
- `uv run pytest tests/utils/test_relations.py -x` — pass (8 passed; coverage-gate failure is expected in a focused run scoped to a single test file).

### Notes for Worker 3

- L3 was deferred per the artifact's own "Defer; the current shape is conservative and the test pins it." Worker 1's recommendation honored verbatim; no edit made.
- L2 (docstring tightening for `"forward_single"`) was bundled into this consolidated single pass per the dispatch instructions — see comment pass below.
- No shadow file was used for the fix implementation. Original source-file line numbers cited throughout.

---

## Comment/docstring pass

L2 applied: `relation_kind`'s docstring at `utils/relations.py:53-55` (now `:53-55` after the edit, structurally equivalent) was tightened so the `"forward_single"` description names `auto_created=False` explicitly. The phrasing now reads `"every other forward single-row relation (ForeignKey, forward OneToOneField — i.e., auto_created=False)"`. This mirrors the framing the artifact recommended so a maintainer reading the `"forward_single"` branch sees the explicit `auto_created=False` contract without having to cross-reference the `"reverse_one_to_one"` branch above. The rest of the docstring is intact.

`uv run ruff format .` and `uv run ruff check --fix .` pass with no further changes after the docstring edit.

---

## Changelog disposition

**Not warranted.** All three cycle edits are internal-only and have no consumer-visible behavior change:

- L1 (drop `@runtime_checkable`): `_RelationFieldLike` is module-private (single-underscore prefix, not exported via `utils/__init__.py`); no external `isinstance(..., _RelationFieldLike)` call site exists in the package. The structural-typing contract for callers is unchanged — `mypy`/`pyright` still enforce the four-flag protocol statically.
- L2 (docstring tightening): pure documentation polish on an existing public function's docstring; no API or behavior change.
- L4 (tighten `kind: object` → `kind: RelationKind | None`): the existing test surface and every production call site already pass `RelationKind` or `None`; the annotation tightening matches what callers were already doing. Runtime semantic (`kind in MANY_SIDE_RELATION_KINDS`) is unchanged. Falls under the "type-annotation tightening inside an existing pinned contract" pattern previously recorded as "not warranted" in worker memory.

Per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" and the active plan's silence on a changelog edit for this artifact, no `CHANGELOG.md` edit was made. The disposition records the reason; the maintainer may revisit if release notes prefer to mention the `_RelationFieldLike` decorator removal alongside the parallel `_DjangoFieldLike` fix from the prior cycle.

---

## Verification (Worker 3)

- L1+L2+L4 accepted; L3 deferred.
- Verification outcome: `cycle accepted; verified`.

Diff confirms: L1 dropped `@runtime_checkable` decorator and removed `runtime_checkable` from the `typing` import; L2 tightened `relation_kind`'s `"forward_single"` docstring branch to add `— i.e., auto_created=False`; L4 tightened `is_many_side_relation_kind`'s `kind: object` annotation to `kind: RelationKind | None`. L3 explicitly deferred per Worker 1's own "Defer; the current shape is conservative and the test pins it." prose. `git diff -- CHANGELOG.md` empty, matching the "not warranted" disposition citing both AGENTS.md ban + active plan's silence. `uv run pytest tests/utils/test_relations.py -x` → 8 passed (coverage-gate failure is expected for a focused single-file run).
