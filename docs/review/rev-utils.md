# Review: `django_strawberry_framework/utils/` (folder pass)

Status: verified

## DRY analysis

- **Existing patterns reused (folder-internal).** The three submodules form a clean leaf set with **zero cross-imports inside `utils/`**: `relations.py` imports only `typing.Literal/Protocol/TypeAlias` (`django_strawberry_framework/utils/relations.py:5`), `strings.py` imports nothing (`django_strawberry_framework/utils/strings.py:1-16`), `typing.py` imports only `typing.Any/get_args/get_origin` (`django_strawberry_framework/utils/typing.py:11`). The folder's `__init__.py` (`django_strawberry_framework/utils/__init__.py:17-19`) is a pure re-export shim — three local imports, one `__all__` tuple, no side effects, no logic. Internal consumers of the subpackage uniformly import from the submodule path, never from the `utils` re-export top-level: `..utils.relations` at `optimizer/field_meta.py:26`, `optimizer/walker.py:14`, `types/resolvers.py:46`, `types/relations.py:24`; `..utils.strings` at `optimizer/walker.py:15`, `types/base.py:42`, `types/converters.py:47`, `types/finalizer.py:46`; `..utils.typing` at `optimizer/extension.py:44`. The `from django_strawberry_framework.utils import …` top-level form is used **only** in tests (`tests/utils/test_relations.py`, `tests/utils/test_strings.py`, `tests/utils/test_typing.py:3`), where it pins the identity-equal re-export contract. The per-file artifacts already established that each helper has exactly one canonical consumer per direction (`rev-utils__relations.md` DRY section; `rev-utils__strings.md` DRY section; `rev-utils__typing.md` DRY section), so this folder pass is observing the seam, not consolidating it.
- **New helpers a fix might justify (folder-internal).** None today. The "queryset submodule will land when queryset-introspection helpers become cross-cutting" sentence in the `__init__.py` docstring at `:13-14` is the explicit charter for the only known forward-extension — and the existing siblings have correctly resisted the pull to absorb adjacent responsibilities (the `_NODEID_STRING_RE` regex candidate logged in `worker-memory/worker-1.md` is still single-site at `types/relay.py` and still gated on "only move to `utils/typing.py` when a second site needs it"). The three siblings each own a single tightly-scoped responsibility (relation-shape classification, case conversion, type-wrapper peel) with no shared abstractions or shared state; there is no fourth helper candidate visible at folder scope.
- **Duplication risk inside the folder.** Negligible. Repeated-literal reports for all three siblings (`docs/shadow/django_strawberry_framework__utils__relations.overview.md`, `…__utils__strings.overview.md:39-41`, `…__utils__typing.overview.md:40-42`) and the `__init__.py` overview (`docs/shadow/django_strawberry_framework__utils____init__.overview.md:38-40`) all surface zero cross-file repeated literals among the four files. The only structural near-pair is the `of_type`-attribute peel concept shared between `unwrap_graphql_type` (`utils/typing.py:28-30`) and `unwrap_return_type` (`utils/typing.py:57-59`) — both branch on `hasattr(x, "of_type")` / `getattr(x, "of_type", None)` — but that within-file pair is correctly factored as two distinct contracts (peel-all vs peel-one, no list-branch vs list-branch) per the per-file artifact's analysis at `rev-utils__typing.md:9`. No cross-file copy-pasted branch logic, no parallel `re.sub(...)` re-derivations, no shadow frozensets duplicating `MANY_SIDE_RELATION_KINDS`.

## High:

None.

## Medium:

### Docstring example-format inconsistency across the three siblings

Per the carry-forwards from `rev-utils__strings.md:L3` and `rev-utils__typing.md:L3`, the three siblings present their `Examples:` blocks in two different formats:

- **Bullet prose** — `utils/relations.py:42-56` uses indented bullet items inside the function docstring's prose. There is no `Examples:` header; the closed-set semantics are explained inline as bullets enumerating each `RelationKind` arm.
- **Arrow + `;` form** — `utils/strings.py:33-36` (`snake_case`), `:63-68` (`pascal_case`), and `utils/typing.py:23-26` (`unwrap_graphql_type`), `:50-55` (`unwrap_return_type`) all use an explicit `Examples:` header followed by indented `"input"` -> `"output"`; lines with a trailing `;` separator and a `.` on the last line.

This is the *third* sibling pass that has flagged the divergence as a folder-scope decision rather than a per-file edit (the carry-forward chain is logged at `worker-memory/worker-1.md` 2026-05-20 entries for `relations.py`, `strings.py`, and `typing.py`). The folder pass owns the decision.

**Decision: standardize on the `Examples:` header + arrow + `;` form.** Rationale:

1. **Four of five docstrings already use it.** `snake_case`, `pascal_case`, `unwrap_graphql_type`, `unwrap_return_type` are all arrow + `;`. Only `relation_kind` uses bullets. Converging to the majority shape minimizes churn (one docstring rewrite vs four).
2. **`Examples:` header is grep-friendly.** A maintainer scanning the codebase for example blocks finds them by header; bullets-without-a-header are invisible to that query.
3. **Arrow + `;` lines parse cleanly as input/output pairs.** The closed-set enumeration in `relation_kind`'s docstring is doing two jobs at once (describing each `RelationKind` arm *and* implicitly listing the inputs that produce it). Converting to the canonical `Examples:` block requires keeping the descriptive prose for each arm (the contract documentation) and adding a parallel `Examples:` block listing illustrative input shapes — i.e., the bullets stay as the prose contract, a new `Examples:` block lists the inputs.

**Recommended edit (next cycle, comment-pass scope).** `utils/relations.py:38-65`: keep the existing bullet block describing the four `RelationKind` arms (the closed-set semantics are load-bearing prose), and append an `Examples:` block underneath listing the canonical input shapes for each branch — e.g., `ManyToManyField`-like → `"many"`; `ManyToOneRel`-like → `"reverse_many_to_one"`; `OneToOneRel`-like → `"reverse_one_to_one"`; `ForeignKey`-like → `"forward_single"`. Use the `field-like-shape → "kind"` form to mirror the input/output framing the other four docstrings use. No code change.

```django_strawberry_framework/utils/relations.py:38:65
def relation_kind(field: _RelationFieldLike) -> RelationKind:
    """Classify a Django relation field by GraphQL/runtime cardinality.

    Four shapes are distinguished:

    - ``"many"`` — forward ``ManyToManyField`` (``many_to_many=True``).
    - ``"reverse_many_to_one"`` — the reverse side of a ``ForeignKey``
      (Django's ``ManyToOneRel`` descriptor: ``one_to_many=True`` paired
      with ``auto_created=True``). [...]
    - ``"reverse_one_to_one"`` — [...].
    - ``"forward_single"`` — every other forward single-row relation
      (``ForeignKey``, forward ``OneToOneField`` — i.e.,
      ``auto_created=False``).
    """
    # ...
```

Severity Medium because three consecutive per-file artifacts forwarded the question to this pass; leaving it unresolved at the folder pass would push it to the project pass where it competes for attention with cross-folder concerns. Medium fits the pattern that `worker-memory/worker-1.md`'s "three-axis-sibling drift IS the bug" calibration captures — the asymmetric outlier (relation_kind's bullets) is Medium even when the practical risk is low, because the doc surface is consumer-facing and the convergence is cheap.

## Low:

### `unwrap_return_type` re-export is public but has zero production callers — keep as-is, document the rationale

Per `rev-utils__typing.md:L1`, `unwrap_return_type` is exported via `django_strawberry_framework/utils/__init__.py:19,28` but a package-wide grep finds zero non-test consumers (confirmed at folder pass: only the definition at `utils/typing.py:33`, the local import at `utils/__init__.py:19`, the `__all__` entry at `:28`, and the test surface at `tests/utils/test_typing.py:4,13,25,37,65`). The per-file artifact deferred the public-vs-private decision to this folder pass.

**Decision: keep `unwrap_return_type` as a public re-export.** Three reasons:

1. **Symmetric sibling contract.** The module docstring at `utils/typing.py:1-9` enumerates two distinct contracts (graphql-core's `NonNull`/`List` `of_type` stacks; Strawberry's `typing.list[T]` vs internal `of_type` wrapper) and explicitly justifies the two-helper split: "Both contracts live here so optimizer and schema factories do not grow parallel unwrap loops." Demoting `unwrap_return_type` to module-private would either (a) leave the docstring lying (it advertises a two-helper public contract) or (b) require rewriting the docstring + the `__init__.py` re-export + the `__all__` tuple + the test imports — a substantially larger surface change than the public-surface footprint warrants.
2. **The schema-factory call site is staged future work.** The module docstring names "schema factories" as a future consumer, and the framework is pre-alpha (per `AGENTS.md` "Pre-alpha. Goal: provide FilterSet, OrderSet, AggregateSet, DjangoType, DjangoConnectionField"). Demoting the helper now would force the next subsystem that needs Strawberry list-peel semantics to re-promote it — adding code-churn for no current gain. This is the inverse situation to `conf.py`'s "don't preemptively populate future-feature settings" rule cited in `worker-memory/worker-1.md`; here the helper *already exists* with a complete test surface and a documented contract, so the "demote then re-promote" round-trip is the more wasteful path.
3. **Test surface is the canonical contract pin.** `tests/utils/test_typing.py:7-13, 16-25, 28-37, 59-65` exhaustively pin every documented branch of `unwrap_return_type` (typing-list, Strawberry-of_type, one-layer-only semantics, no-wrapper passthrough). The contract is grep-discoverable from both ends today; demoting would break the `from django_strawberry_framework.utils import unwrap_return_type` test import surface and force the test path to use `from django_strawberry_framework.utils.typing import _unwrap_return_type` — a leaky-private-name pattern that worker-memory has previously calibrated as worse than a public-with-no-current-consumer surface.

**Action: no code change.** Document the rationale in the `__init__.py` module docstring at `utils/__init__.py:9-11` — add a one-sentence parenthetical note that `unwrap_return_type` is the Strawberry-list-peel sibling of `unwrap_graphql_type` and is exported for the upcoming schema-factory consumer, mirroring the `__init__.py:13-14` `queryset` future-extension framing. Low severity because the surface is correct on its own terms and the test pin holds the contract; this is documentation polish, not a structural change. Comment-pass scope.

```django_strawberry_framework/utils/__init__.py:1:15
"""Cross-cutting utility helpers.

Subpackage structure mirrors the convention both `graphene_django/utils/`
and `strawberry_django/utils/` converge on: focused submodules per
concern rather than a single 500-line `utils.py`. Currently:

- ``relations`` — Django relation-shape classification
  (``relation_kind``, ``RelationKind``, ``is_many_side_relation_kind``).
- ``strings`` — case conversion (``snake_case``, ``pascal_case``).
- ``typing`` — Strawberry / Python / GraphQL type unwrapping
  (``unwrap_graphql_type``, ``unwrap_return_type``).

A ``queryset`` submodule will land when queryset-introspection helpers
become cross-cutting (currently each subsystem keeps its own).
"""
```

### `__init__.py` re-exports `MANY_SIDE_RELATION_KINDS` only via the module path, not the package top-level

`MANY_SIDE_RELATION_KINDS` at `utils/relations.py:14-19` is the canonical frozenset for the many-side rule, but it is not re-exported through `utils/__init__.py:17` (only `RelationKind`, `is_many_side_relation_kind`, and `relation_kind` are pulled into the top-level surface). Consumers who need the set directly would have to import from `..utils.relations` rather than `..utils`. Today there are zero such consumers (every reader uses `is_many_side_relation_kind(kind)` instead of `kind in MANY_SIDE_RELATION_KINDS` directly — verified at folder pass), so the omission is correct: the public surface routes through the predicate, not the underlying set. The data structure is an implementation detail of the predicate.

**Action: no change.** This is the right shape — the helper is the public seam, the frozenset is the helper's storage. The Low is flagged only because a future maintainer adding `MANY_SIDE_RELATION_KINDS` to `__all__` (e.g., for "completeness") would be widening the public surface unnecessarily; the omission is intentional and worth pinning in the `__init__.py` docstring's `relations` bullet at `:7-8` ("relation-shape classification" already conveys this — no edit needed, but flagging for awareness). No edit recommended.

```django_strawberry_framework/utils/__init__.py:17:29
from .relations import RelationKind, is_many_side_relation_kind, relation_kind
from .strings import pascal_case, snake_case
from .typing import unwrap_graphql_type, unwrap_return_type

__all__ = (
    "RelationKind",
    "is_many_side_relation_kind",
    "pascal_case",
    "relation_kind",
    "snake_case",
    "unwrap_graphql_type",
    "unwrap_return_type",
)
```

### One-way dependency direction inside the folder is exemplary — no circular-import risk

The three submodules have **zero** imports from each other: `relations.py` imports stdlib only; `strings.py` imports nothing; `typing.py` imports stdlib only. The `__init__.py` imports each submodule with one local-relative line. The folder is a fan-out leaf with no internal cycles, no shared state, and no internal abstractions. This is the structural ideal for a `utils/` subpackage and is worth recording as the reference shape — but it carries no actionable recommendation. Flagging as Low only to anchor the "no internal coupling" invariant in writing so a future maintainer who proposes introducing a `utils/_shared.py` or a cross-helper utility has to argue *why* the current zero-coupling shape should be broken.

```django_strawberry_framework/utils/relations.py:5:5
from typing import Literal, Protocol, TypeAlias
```

```django_strawberry_framework/utils/typing.py:11:11
from typing import Any, get_args, get_origin
```

## What looks solid

- **`__init__.py` is a pure re-export shim.** `django_strawberry_framework/utils/__init__.py:17-29` is three import lines + one `__all__` tuple + a module docstring. No logic, no side effects, no module-level state, no import-time work beyond the three submodule loads. The overview at `docs/shadow/django_strawberry_framework__utils____init__.overview.md:14-40` reports zero symbols, zero control-flow hotspots, zero Django/ORM markers, zero calls of interest, zero repeated literals. Reference shape for a leaf-subpackage `__init__.py`.
- **`__all__` is alphabetically ordered.** `utils/__init__.py:21-29` lists all seven re-exports in alphabetical order — `RelationKind` (uppercase R sorts after lowercase letters via PEP 8 convention, but here `R` is the only uppercase entry and is correctly placed at the top by Python's lexicographic comparison of the all-string tuple). The alphabetic ordering is consistent with the `import` lines that precede it (`relations` before `strings` before `typing`), and makes additions diff-clean.
- **Submodule docstrings name their charters.** Each submodule's module docstring states its single responsibility and the call sites it serves: `relations.py:1` ("Relation-shape helpers shared by converters, resolvers, and the optimizer"), `strings.py:1-16` (case-conversion with the two-direction GraphQL/Django boundary justification), `typing.py:1-9` (the two distinct contracts — graphql-core wrapper stacks vs Strawberry list-wrapper). The `__init__.py:1-15` docstring then enumerates all three at folder scope. Five docstrings, one coherent story.
- **No cross-folder writes from `utils/`.** The folder has zero outbound writes to other packages — no `..optimizer`, no `..types`, no `..registry`, no `..conf`, no `..exceptions` imports anywhere in the four files. It is a true leaf, sourcing only from stdlib `typing`. Confirmed at folder pass by grep across all three submodules.
- **Per-file artifacts converged on the same finding shape.** `rev-utils__relations.md`, `rev-utils__strings.md`, and `rev-utils__typing.md` all landed 0 High / 0 Medium / 3-4 Low — the canonical leaf-module shape. The Lows are docstring polish, test-pin reinforcement, and dead-decorator weight removal. No structural defects, no DRY duplication, no Django ORM correctness concerns. The folder-pass Medium (docstring example format) is the one concern that genuinely required folder-scope context (a three-sibling decision); the other three Lows here are awareness pins, not actionable edits.
- **Helper ran cleanly on every sibling.** Per `worker-1.md`, the static helper is optional under `utils/`; ran anyway on all four files (`relations.py`, `strings.py`, `typing.py`, `__init__.py`) because the folder pass requires sibling overviews for the repeated-literal check. Every overview confirmed "Repeated string literals: None." and no Django/ORM markers — consistent with the leaf-module charter.
- **Subpackage charter quoting convention matches the `types/` subpackage shape established at `rev-types.md`.** The `utils/__init__.py` docstring enumerates each submodule with a backtick name + en-dash + responsibility + parenthetical re-export list. This mirrors the convention from the `types/__init__.py` docstring (per `rev-types.md`'s folder pass) — useful for a future maintainer reading both subpackage docstrings to understand the layout. Cross-folder doc-shape consistency.

### Summary

`utils/` is a three-submodule leaf subpackage (`relations.py` 70 lines, `strings.py` 70 lines, `typing.py` 62 lines, `__init__.py` 29 lines) with zero internal coupling, zero ORM markers, zero side effects at import time, and a clean fan-out dependency direction. The `__init__.py` is a pure re-export shim with no logic. Per-file artifacts landed 0 High / 0 Medium / 3-4 Low each, all docstring polish or awareness pins. **Folder-pass findings: 0 High / 1 Medium / 3 Low.** The single Medium (M1) is the docstring example-format inconsistency forwarded from `rev-utils__strings.md` L3 and `rev-utils__typing.md` L3 — three consecutive per-file artifacts deferred the question to this folder pass, and the decision is to standardize on the `Examples:` header + arrow + `;` form already used by four of the five function docstrings. The three Lows are: (L1) keep `unwrap_return_type` as a public re-export and document the rationale in `utils/__init__.py` (forwarded from `rev-utils__typing.md` L1); (L2) `MANY_SIDE_RELATION_KINDS` is correctly *not* re-exported at the package top-level (awareness pin); (L3) one-way dependency direction inside the folder is exemplary (awareness pin for any future internal-coupling proposal). No DRY duplication, no logic bugs, the subpackage is the reference shape for a small leaf `utils/` folder paired with three single-responsibility helper modules.

---

## Fix report (Worker 2)

Consolidated single Worker 2 spawn (logic + comment + changelog) — the artifact lands 0H/1M/3L and every in-cycle change is docstring-only, so separate passes would be ceremony with no edits to verify between them.

### Files touched

- `django_strawberry_framework/utils/relations.py:38-71` — M1: appended an `Examples:` block to the `relation_kind` docstring listing the canonical input shapes for each `RelationKind` arm in the arrow + `;` form, matching the style used by `utils/strings.py:33-36, 63-68` and `utils/typing.py:23-26, 50-55`. The existing bullet block describing the four arms (the closed-set semantics are load-bearing prose) is preserved per the artifact's recommendation at `rev-utils.md:30-32`.
- `django_strawberry_framework/utils/__init__.py:10-15` — L1: extended the `typing` bullet to note that `unwrap_return_type` is the Strawberry-list-peel sibling of `unwrap_graphql_type`, exported for the upcoming schema-factory consumer, mirroring the `queryset` future-extension framing already below the bullet block.

### Tests added or updated

- None. Both edits are docstring-only with no behavior change. The existing test surface (`tests/utils/test_relations.py`, `tests/utils/test_typing.py`) already pins every documented branch of the affected functions.

### Validation run

- `uv run ruff format .` — pass (101 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).
- `pytest` — not run per dispatch.

### Notes for Worker 3

- M1: bullet block at `utils/relations.py:42-55` is preserved unchanged — the closed-set semantics are the contract documentation, the new `Examples:` block names the canonical input shapes per the artifact's "keep the existing bullet block ... and APPEND an `Examples:` block underneath" instruction at `rev-utils.md:30-32`.
- L1: the new sentence is appended to the existing `typing` bullet rather than inserted as a new bullet so the per-submodule bullet block reads as one entry per submodule (matches the `relations` and `strings` bullets' shape). The "mirrors the `queryset` future-extension framing below" cross-reference is the artifact's explicit framing at `rev-utils.md:65-66`.
- L2 (`MANY_SIDE_RELATION_KINDS` not re-exported at package top-level): no change per artifact — the omission is intentional, the helper `is_many_side_relation_kind` is the public seam, and the frozenset is the helper's storage. Recording-only disposition.
- L3 (one-way dependency direction inside the folder is exemplary): no change per artifact — awareness pin anchoring the "no internal coupling" invariant in writing for any future maintainer who proposes introducing a `utils/_shared.py` or a cross-helper utility. Recording-only disposition.

---

## Verification (Worker 3)

### Logic verification outcome

Every folder-pass finding addressed or recorded as intentional no-change:

- **M1 (docstring example-format inconsistency)** — applied. `utils/relations.py:57-61` now appends an `Examples:` block underneath the existing bullet block, listing the canonical input shapes for each `RelationKind` arm in the arrow + `;` form (`ManyToManyField`-like -> `"many"`; `ManyToOneRel`-like -> `"reverse_many_to_one"`; `OneToOneRel`-like -> `"reverse_one_to_one"`; `ForeignKey`-like -> `"forward_single"`). The pre-existing bullet block at `utils/relations.py:43-55` (closed-set contract semantics) is preserved unchanged per the artifact's "keep the bullet block, append Examples underneath" instruction at `rev-utils.md:30-32`. The new block matches the arrow + `;` shape used by `utils/strings.py:34-37,72-78`, `utils/typing.py:23-25,62-67` — three-axis sibling docstring shape now converges to the majority form.
- **L1 (`unwrap_return_type` re-export rationale)** — applied. `utils/__init__.py:12-14` extends the existing `typing` bullet with a three-line sentence naming `unwrap_return_type` as the Strawberry-list-peel sibling of `unwrap_graphql_type` and citing the upcoming schema-factory consumer (mirrors the `queryset` future-extension framing at `:16-17`). Appended to the existing bullet rather than added as a new bullet — matches the per-submodule bullet shape used by `relations` and `strings` siblings.
- **L2 (`MANY_SIDE_RELATION_KINDS` not re-exported at package top-level)** — recording-only, no edit per the artifact's explicit "no change" disposition at `rev-utils.md:88-91`. Verified: `utils/__init__.py:20,24-32` still re-exports only `RelationKind`, `is_many_side_relation_kind`, `relation_kind` from `relations`; `MANY_SIDE_RELATION_KINDS` remains module-private storage behind the `is_many_side_relation_kind` predicate. The intentional omission is preserved.
- **L3 (one-way dependency direction inside the folder)** — recording-only, no edit per the artifact's "awareness pin" framing at `rev-utils.md:108-114`. Verified: `relations.py:5` imports stdlib `typing` only; `strings.py` imports nothing; `typing.py:11` imports stdlib `typing` only; `__init__.py:20-22` imports only the three submodules. Zero internal coupling, zero cross-folder writes — the leaf-subpackage invariant is preserved.

### DRY findings disposition

Folder-pass DRY analysis at `rev-utils.md:5-9` concluded the subpackage has zero cross-file repeated literals, zero internal coupling, zero outbound writes to other packages. The single Medium (M1) was itself a DRY convergence — three-sibling docstring shape now converges on the arrow + `;` form already used by four of five function docstrings. No new helpers extracted, no consolidation needed — the per-file passes had already consolidated locally. The folder pass is the recording site for the cross-sibling decision (docstring format), not a structural refactor.

### Temp test verification

None used. Both in-cycle edits are docstring-only with no behavior change; the existing test surface (`tests/utils/test_relations.py`, `tests/utils/test_typing.py`) already pins every documented branch of the affected functions, and no new branch was introduced. Empty `git diff -- CHANGELOG.md` confirmed.

### Verification outcome

`cycle accepted; verified`

The consolidated single-spawn pass (logic + comment + changelog) is the right shape for a folder pass landing 0H/1M/3L where every in-cycle edit is docstring-only. Verification reduces to: (a) confirm `git diff -- CHANGELOG.md` is empty — confirmed; (b) confirm the source diff is confined to `utils/relations.py` (M1) and `utils/__init__.py` (L1) with no fresh edits in unrelated files — confirmed; (c) confirm L2 + L3 are preserved as recording-only with no edit; (d) confirm the M1 edit appends an `Examples:` block (not a replacement of the bullet block) matching the artifact's "keep ... and append" instruction; (e) confirm L1 extends the existing `typing` bullet rather than adding a new bullet, mirroring the `queryset` future-extension framing already in the docstring. All five gates pass. Changelog disposition "not warranted" cites both the AGENTS.md ban and the active plan's lack of authorization — accept threshold met.

---

## Comment/docstring pass

Combined into the consolidated single pass above. Both in-cycle edits (M1 and L1) are docstring-only by construction, so the comment pass and the logic pass collapse into the same Edit calls. No additional docstring changes beyond M1 + L1 — L2 and L3 are recording-only with no edit per the artifact's explicit "no edit recommended" / "no change" dispositions at `rev-utils.md:90` and `rev-utils.md:108-114`.

---

## Changelog disposition

**Not warranted.** Both edits are docstring-only:

- M1 appends an `Examples:` block to a function docstring; no public-symbol add/remove, no behavior change, no consumer-visible surface change.
- L1 extends a module docstring with a one-sentence cross-reference to an already-public re-export; the re-export itself (`unwrap_return_type` at `utils/__init__.py:19,28`) is unchanged.

Per the consolidated-patterns calibration in `worker-memory/worker-2.md` ("not warranted (default for ... docstring polish ...)") and `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" + active-plan silence: no `CHANGELOG.md` edit made.

---

## Iteration log

_Append-only — Worker 2 / Worker 3 re-passes attach here._
