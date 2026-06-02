# Review: `django_strawberry_framework/utils/`

Status: verified

Folder pass over the three-submodule `utils/` subpackage plus its `__init__.py` (4 files, 249 total source lines). Sibling artifacts read first: `rev-utils__relations.md` (Status: verified), `rev-utils__strings.md` (Status: verified), `rev-utils__typing.md` (Status: verified). All three closed under shape #5 except `rev-utils__relations.md` which closed under shape #4 (single docstring edit on `relation_kind`'s L1 reachability gap).

## DRY analysis

- None — every per-file `## DRY analysis` artifact closed at folder-pass-relevant scope: `rev-utils__relations.md` "None — the module is the single canonical home for the four-branch Django cardinality classifier"; `rev-utils__strings.md` carried one defer-with-trigger DRY bullet (cross-folder `_camel_case` extraction) gated on the 0.0.8 cycle's `orders/` review per the second-closing-folder calibration; `rev-utils__typing.md` "None — the module IS the canonical extraction." No within-folder helper duplication exists: `relations.py`, `strings.py`, and `typing.py` each own a single concern (Django relation cardinality, GraphQL/Django case conversion, type-wrapper unwrapping) with zero cross-submodule overlap. Cross-folder repeated-literal sweep (`from .utils.relations`, `from .utils.strings`, `from .utils.typing` consumer imports) confirms exactly one import path per consumer per helper — no parallel re-derivation anywhere. The single cross-folder act-now-eligible DRY opportunity (the `_camel_case` extraction) is gated on `orders/` being in scope; `orders/` is concurrent spec-028 Slice 3 maintainer work landing post-baseline (commit `b8fbd74`) and is NOT in the 0.0.7 review plan, so the deferral phrasing from `rev-utils__strings.md` stands verbatim and is recorded in `## What looks solid > ### DRY recap` below for cross-cycle audit-trail continuity.

## High:

None.

## Medium:

None.

## Low:

### L1 — Trio of submodule `__all__`-gap deferrals confirmed at folder scope; do not act at folder scope

All three sibling artifacts (`rev-utils__relations.md::L3`, `rev-utils__strings.md::L3`, `rev-utils__typing.md::L4`) recorded the same forward-looking Low: each submodule (`utils/relations.py`, `utils/strings.py`, `utils/typing.py`) lacks a submodule-level `__all__`. The package-level `utils/__init__.py:24-32` carries the canonical `__all__` re-export tuple covering all seven exported symbols (`RelationKind`, `is_many_side_relation_kind`, `pascal_case`, `relation_kind`, `snake_case`, `unwrap_graphql_type`, `unwrap_return_type`). Each per-file artifact deferred with explicit trigger phrasing: "sibling utils submodules grow an `__all__` or when a [third/fourth] public symbol lands."

Package-wide convention audit (grep `^__all__` across `django_strawberry_framework/`): submodule-level `__all__` is the exception, not the rule. Only `optimizer/extension.py:68`, `exceptions.py:8`, `list_field.py:22`, and `sets_mixins.py:127` (top-level modules) carry submodule `__all__`. Every submodule under `filters/` (`base.py`, `factories.py`, `inputs.py`, `sets.py`), every submodule under `types/` (`base.py`, `converters.py`, `definition.py`, `finalizer.py`, `relations.py`, `relay.py`, `resolvers.py`), every other submodule under `optimizer/` (`_context.py`, `field_meta.py`, `hints.py`, `plans.py`, `walker.py`), and the lone submodule under `testing/` (`_wrap.py`) all lack submodule `__all__`. The package-level `__init__.py` per subpackage is the canonical curation site.

Landing `__all__` on all three `utils/*.py` submodules at this folder pass would create a single-folder anomaly inside the package: `utils/` would become the only subpackage with uniform submodule `__all__` adoption. The trigger phrase ("sibling utils submodules grow an `__all__`") is NOT satisfied — the trio is in lockstep, but the lockstep is the package-wide default state, not a deferred parity gap. Per the memory calibration "when three sibling submodules all defer the same parity-Low with the same trigger, the folder pass either resolves the trigger (act-now on all three) or restates the explicit-trio-defer in `## What looks solid > ### DRY recap`": this folder pass continues the explicit-trio-defer.

Restated folder-pass trigger condition (supersedes the three per-file trigger phrasings): "Defer until either (a) the package adopts a uniform submodule `__all__` convention as a package-wide cleanup pass (most likely at a major-version-bump release boundary), OR (b) any utils submodule grows a fourth public symbol where the internal-helper / public-symbol split inside the submodule becomes load-bearing." The current `_RelationFieldLike` (`relations.py:19-32`) and `MANY_SIDE_RELATION_KINDS` (`relations.py:14-16`) leading-underscore-or-internal symbols are gated only by Python's `_` convention and the package-level `utils/__init__.py:24-32` curation, which today is sufficient — `from django_strawberry_framework.utils.relations import *` is not a documented entrypoint and no consumer uses it.

Citation hygiene only — behaviour preserved. Folder-scope coordination point landed; this Low is the audit-trail closure of the three sibling forwards.

### L2 — `utils/__init__.py:11-14` "exported for the upcoming schema-factory consumer" framing for `unwrap_return_type` carries the same audit-trail risk flagged at `rev-utils__typing.md::L5`

`utils/__init__.py:10-14` reads:

```
- ``typing`` — Strawberry / Python / GraphQL type unwrapping
  (``unwrap_graphql_type``, ``unwrap_return_type``).
  ``unwrap_return_type`` is the Strawberry-list-peel sibling of
  ``unwrap_graphql_type``, exported for the upcoming schema-factory
  consumer (mirrors the ``queryset`` future-extension framing below).
```

`rev-utils__typing.md::L5` (verified) records the same audit-trail concern: `unwrap_return_type` has zero current production consumers; the export is staged for an upcoming schema-factory consumer that has not landed. The trigger phrased in `rev-utils__typing.md::L5` is "version bumps to 0.0.9 without a non-test call site of `unwrap_return_type` landing in `django_strawberry_framework/`." At folder scope, the same audit applies to the `utils/__init__.py` re-export site itself: the module docstring framing AND the `__all__` entry are both speculative-API surface today.

The `queryset` future-extension framing at `utils/__init__.py:16-17` is in the same shape — a submodule that will land "when queryset-introspection helpers become cross-cutting" — and is also referenced at `docs/GLOSSARY.md:1171` as "Shared queryset introspection helpers (`utils/queryset.py`) — `BETTER` item 36" (the BACKLOG entry confirms this is a deliberately-staged future API).

Defer until the same trigger fires as `rev-utils__typing.md::L5` — version bumps to 0.0.9 without a non-test call site of `unwrap_return_type` landing — at which point both the `utils/__init__.py` framing AND the re-export warrant a YAGNI re-evaluation together. Trigger condition is verbatim from the sibling Low; folder-scope restatement is purely for audit-trail continuity across the per-file → folder-pass boundary. Citation hygiene only — behaviour preserved.

### L3 — Module docstring's `queryset` future-extension framing has had no card / spec / BETTER-item tag landed in the source comment for cross-reference

`utils/__init__.py:16-17` reads:

```
A ``queryset`` submodule will land when queryset-introspection helpers
become cross-cutting (currently each subsystem keeps its own).
```

The trigger condition is implicit ("when queryset-introspection helpers become cross-cutting"). The matching BACKLOG entry is at `docs/GLOSSARY.md:1171` ("Shared queryset introspection helpers (`utils/queryset.py`) — `BETTER` item 36"). Adding the `BETTER item 36` citation to the source comment would make the cross-reference explicit and let a future cycle grep from either end. This is purely a documentation-hygiene Low — the framing is correct prose, just not greppable from the source side.

Defer until the next time `utils/__init__.py` is edited for any reason (e.g. when the third public symbol or schema-factory consumer lands and the framing is updated). Mirrors the AGENTS.md #28 / #27 citation-hygiene calibration from `worker-memory/worker-1.md`'s consolidated calibrations: "Stale `spec-NN` citations / `TODO-ALPHA-NN` anchors … are Low (citation hygiene), not Medium, when the prose the citation supports is correct." Here the prose IS correct; the cross-reference tag is just absent. Citation hygiene only — behaviour preserved.

## What looks solid

### DRY recap

- **Existing patterns reused.** The three submodules under `utils/` are each a single-concern canonical-home extraction with uniform consumer-import shapes: `relations.py` is the single home of the four-branch Django relation cardinality classifier (`relation_kind`) and its closed-`Literal` type alias (`RelationKind`) plus the membership-set source of truth (`MANY_SIDE_RELATION_KINDS`) and predicate (`is_many_side_relation_kind`); consumed via `from ..utils.relations import …` at `optimizer/walker.py:14`, `optimizer/field_meta.py:26, 31`, `types/relations.py:24`, `types/resolvers.py:50`. `strings.py` is the single home of two-direction case conversion (`snake_case` reverses Strawberry camelCase → Django snake_case; `pascal_case` builds GraphQL-friendly type names from Django snake_case); consumed via `from ..utils.strings import …` at `optimizer/walker.py:15`, `types/base.py:42`, `types/finalizer.py:56`, `types/converters.py:52`, `sets_mixins.py:34`. `typing.py` is the single home of two unwrap helpers (`unwrap_graphql_type` deep `of_type`-peel for graphql-core / Strawberry wrapper stacks; `unwrap_return_type` one-layer `of_type`-or-`list[T]`-peel staged for the upcoming schema factory); consumed via `from ..utils.typing import …` at `optimizer/extension.py:45`. Every consumer reads through the canonical site.
- **New helpers considered.** Folder-scope candidates evaluated and rejected: (1) a shared `_get_flag(field, attr) -> bool` defensive-`getattr` wrapper for the five `getattr(field, "<flag>", False)` repetitions in `relations.py:69-75` — rejected per `rev-utils__relations.md` "Duplication risk in the current file" recap because each call reads a distinct attribute and folding through a helper would obscure the branch structure; (2) a shared `_non_empty_segments(name) -> list[str]` helper for the `name.split("_")` filter shape used by `pascal_case` and a hypothetical future `camel_case` — rejected per `rev-utils__strings.md` "New helpers considered" recap because the segment-filter shape is a one-liner that reads more clearly inline; (3) a combined `unwrap(rt, *, deep=False)` dispatcher folding `unwrap_graphql_type` and `unwrap_return_type` behind a kwarg — rejected per `rev-utils__typing.md` "New helpers considered" recap because the two helpers have different termination conditions and different docstring contracts. All three rejections survive at folder scope: same reasoning applies; folder-pass does not introduce new factoring incentives.
- **Duplication risk in the current file.** None within `utils/`. The cross-folder `_camel_case` duplication at `filters/inputs.py:783-789` and `orders/inputs.py:164-170` is byte-identical (only docstring example varies: `galaxy_name` vs `shelf_code`); `utils/strings.py` module docstring at `:13-15` explicitly hosts the canonical-home framing for case-conversion ("Kept minimal on purpose. If a third style ever shows up we'll add it here rather than re-deriving inline at the call site"). The defer-with-trigger from `rev-utils__strings.md::DRY analysis` is restated verbatim for cross-cycle audit-trail: **defer until the 0.0.8 cycle's `orders/` review closes; the cycle that closes `orders/` second owns the extraction per the second-closing-folder calibration. The trigger is satisfied today (two sites exist); the deferral is for cycle-boundary hygiene, not factoring uncertainty.** When the 0.0.8 cycle opens, fold both `_camel_case` helpers through a new `utils/strings.py::camel_case(name)` and update `utils/__init__.py::__all__` to re-export it.

### Other positives

- **Folder-pass `__init__.py` audit.** `utils/__init__.py:1-32` (32 lines) is a focused public-surface curator: 18-line module docstring naming each submodule and its public symbols + future-extension framing for `queryset`; three `from .submodule import …` re-export lines (`:20-22`); seven-symbol alphabetical `__all__` tuple (`:24-32`). The module docstring explicitly references `graphene_django/utils/` and `strawberry_django/utils/` convention ("Subpackage structure mirrors the convention both … converge on: focused submodules per concern rather than a single 500-line `utils.py`") — same convention discipline as the sibling subpackage `__init__.py` shapes recorded in `rev-types.md` and `rev-optimizer.md`. No imports beyond the three local re-exports; zero runtime cost; clean public/private separation. Static helper output (`docs/shadow/django_strawberry_framework__utils____init__.overview.md`): 3 imports, 0 symbols, 0 control-flow hotspots, 0 calls of interest, 0 repeated literals, 0 TODOs.
- **Import-direction audit (one-way, no cycles, no within-folder cross-deps).** Each `utils/` submodule imports only from the Python standard library (`typing.Literal`, `typing.Protocol`, `typing.TypeAlias` in `relations.py`; nothing in `strings.py`; `typing.Any`, `typing.get_args`, `typing.get_origin` in `typing.py`) plus `from __future__ import annotations` in `relations.py`. Zero first-party imports; zero Django imports; zero Strawberry imports; zero cross-submodule imports within `utils/`. This is the right factoring for a leaf-utility subpackage consumed across `optimizer/`, `types/`, `filters/`, `sets_mixins.py` — guaranteed circular-import-free regardless of how the rest of the package's import graph evolves. Per the memory calibration "import-direction audit at types/ folder. Strict-DAG: types/ consumes ..optimizer / ..exceptions / ..registry / ..utils / ..scalars (leaf-direction)" — `utils/` is the strictest leaf of all: no first-party imports at all.
- **Cross-file repeated-literal check (folder-pass mandatory).** Comparing `Repeated string literals` sections of all four sibling overviews: `utils/__init__.py` (zero); `utils/relations.py` has four repeated literals (`reverse_many_to_one` 3×, `reverse_one_to_one` 2×, `forward_single` 2×, `auto_created` 2×) but each is internal to the `RelationKind` Literal alias and the `relation_kind` branch returns — no cross-file duplication; `utils/strings.py` (zero); `utils/typing.py` (zero). No folder-level DRY candidate from repeated-literal duplication. The four `RelationKind` literal-string occurrences inside `relations.py` itself are the load-bearing single-source-of-truth — every consumer reads the literal through the closed-`Literal` type alias, not by retyping the string.
- **GLOSSARY drift quick-check (folder scope).** All seven exported public symbols (`RelationKind`, `is_many_side_relation_kind`, `pascal_case`, `relation_kind`, `snake_case`, `unwrap_graphql_type`, `unwrap_return_type`) are correctly absent from `docs/GLOSSARY.md` as backticked symbol names per the consolidated calibration "Internal-mechanics GLOSSARY absence is correct convention" — consumer contract surfaces through `Relation handling` (GLOSSARY.md:888-926) for relation cardinality, `auto_camel_case` as a `StrawberryConfig` kwarg (GLOSSARY.md:1085, 1090) for case-conversion, and the `DjangoOptimizerExtension` and upcoming schema-factory surfaces for type-unwrapping. The single forward-extension reference is at `docs/GLOSSARY.md:1171` ("Shared queryset introspection helpers (`utils/queryset.py`) — `BETTER` item 36") naming the future `utils/queryset.py` submodule explicitly. No GLOSSARY drift to forward to project pass.
- **Static helper coverage (folder-pass mandatory).** Plan-time `--all` sweep left `utils/__init__.py` and `utils/relations.py` overviews missing from `docs/shadow/` (the `--all` sweep regenerated `utils/strings.py` and `utils/typing.py` but skipped the `__init__.py` and `relations.py`). This Worker 1 spawn ran `python scripts/review_inspect.py django_strawberry_framework/utils/__init__.py --output-dir docs/shadow` and `python scripts/review_inspect.py django_strawberry_framework/utils/relations.py --output-dir docs/shadow` once each to materialise the missing overviews ahead of the folder-pass repeated-literal sweep. Shadow files are gitignored; only this artifact is tracked.
- **Test-coverage discipline (folder scope).** Each submodule has a dedicated test file under `tests/utils/`: `tests/utils/test_relations.py` (7 tests pinning all four `RelationKind` branches plus the literal enumeration audit plus the `is_many_side_relation_kind` per-kind sweep plus the re-export identity assertion), `tests/utils/test_strings.py` (3 tests pinning `snake_case` happy paths, `pascal_case` happy paths, and `pascal_case` silent-empty contract), `tests/utils/test_typing.py` (8 tests pinning both helpers' happy paths plus branch coverage for bare `list`, bare `typing.List`, Strawberry-style `of_type`, wrapper-precedence rule, recursive `of_type`-peel, bare-class passthrough, and `None` passthrough). Every public surface symbol is pinned; every branch in every helper is covered. The `tests/utils/test_relations.py::test_utils_init_reexports_match_submodule` test pins identity (not just equality) for all three `utils/__init__.py` re-exports of `relations.py` symbols — catching any accidental wildcard re-import or future shim wrapping the helpers.
- **`from __future__ import annotations` discipline is correctly applied per-file.** `utils/relations.py` uses it (`:3`) because the Protocol bases and the closed-`Literal` type alias benefit from forward-reference-only annotations and the `Protocol` runtime import (`:5`) is purely for class-definition base class purposes. `utils/typing.py` does not use it because both helpers use only `typing.Any` and the standard `get_args`/`get_origin` runtime calls. `utils/strings.py` does not use it because both helpers use only built-in `str` annotations. Each module's import discipline matches the memory calibration "`get_type_hints` / `from __future__ import annotations` discipline. Modules with no internal-type forward references and no `TYPE_CHECKING`-guarded imports do not need the future-annotations directive."
- **Per-helper docstring acronym-caveat discipline.** Each public helper carries a docstring caveat naming inputs unreachable from the documented call chain so a future direct consumer is not surprised: `relations.py::relation_kind:54-61` (`one_to_many=True, auto_created=False` defensive fallback) added in this cycle's `rev-utils__relations.md` L1 fix; `strings.py::snake_case:26-31` (`HTMLParser` → `h_t_m_l_parser` acronym); `strings.py::pascal_case:53-61` (`my_HTTP_response` → `MyHttpResponse` acronym); `typing.py::unwrap_graphql_type:23-26` (worked example block with `NonNull(List(NonNull(Inner)))` → `Inner` plus `None` passthrough); `typing.py::unwrap_return_type:50-55` (worked example block with the `list[list[int]]` → `list[int]` "chain calls if you need full unwrapping" guidance plus the `StrawberryList(of_type=int)` happy path). Every public-surface helper meets the "Test-double surfaces are documented" calibration from `worker-memory/worker-1.md`.

### Summary

`utils/` is a 249-line three-submodule leaf-utility subpackage hosting three single-concern canonical-home helpers (Django relation cardinality classification in `relations.py`; two-direction GraphQL/Django case conversion in `strings.py`; graphql-core / Strawberry wrapper-stack type unwrapping in `typing.py`) plus a 32-line public-surface curator `__init__.py`. Every consumer of every helper across `optimizer/`, `types/`, `filters/`, and `sets_mixins.py` imports through the canonical site; no parallel implementations exist anywhere in the package; the subpackage is strictly leaf (zero first-party imports, zero Django runtime imports, zero Strawberry runtime imports). Zero High, zero Medium, three forward-looking Lows: L1 closes the trio-cut on submodule `__all__` deferrals by restating a folder-scope trigger that supersedes the three per-file phrasings (do not act at folder scope; package-wide convention is that submodule `__all__` is the exception, not the rule); L2 restates the audit-trail concern from `rev-utils__typing.md::L5` at the folder-scope `utils/__init__.py` re-export site; L3 flags a citation-hygiene gap where the `utils/__init__.py:16-17` `queryset` future-extension framing could cite `BETTER item 36` for greppable cross-reference. One cross-folder defer-with-trigger DRY opportunity (`_camel_case` extraction from `filters/inputs.py` and `orders/inputs.py` through a new `utils/strings.py::camel_case`) restated verbatim from `rev-utils__strings.md` in the `### DRY recap` audit trail; gated on the 0.0.8 cycle's `orders/` review per the second-closing-folder calibration. Folder pass qualifies for shape #5 (no-source-edit cycle, skip Worker 2): zero High, no behaviour-changing Medium, every Low is forward-looking-without-edit, no GLOSSARY-only fix in scope, zero source/test/docstring edits.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (213 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!; one pre-existing COM812-vs-formatter warning unrelated to this artifact).

### Notes for Worker 3
- Shape #5 folder pass. Zero edits to `django_strawberry_framework/utils/__init__.py`, `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/utils/typing.py`, `tests/utils/test_relations.py`, `tests/utils/test_strings.py`, `tests/utils/test_typing.py`. All three sibling per-file artifacts (`rev-utils__relations.md`, `rev-utils__strings.md`, `rev-utils__typing.md`) closed at `Status: verified` before this folder pass spawned.
- L1 (trio-cut on submodule `__all__`): folder-scope decision is **do not act**. Restated trigger condition supersedes the three per-file deferrals: "Defer until either (a) the package adopts a uniform submodule `__all__` convention as a package-wide cleanup pass, OR (b) any utils submodule grows a fourth public symbol where the internal-helper / public-symbol split inside the submodule becomes load-bearing." Reasoning: package-wide convention audit confirms submodule `__all__` is the exception, not the rule — only `optimizer/extension.py`, `exceptions.py`, `list_field.py`, `sets_mixins.py` carry submodule `__all__`; every submodule under `filters/`, every submodule under `types/`, every other submodule under `optimizer/`, and the lone submodule under `testing/` lack one. Acting on `utils/*.py` would create a single-folder anomaly.
- L2 (`unwrap_return_type` zero-current-production-consumer paper-trail at folder-scope `utils/__init__.py`): forwarded with same trigger as `rev-utils__typing.md::L5` — "version bumps to 0.0.9 without a non-test call site of `unwrap_return_type` landing in `django_strawberry_framework/`." Folder-pass restatement is purely audit-trail continuity.
- L3 (`queryset` future-extension framing missing `BETTER item 36` cross-reference tag): forwarded with trigger "next edit to `utils/__init__.py` for any reason." Pure citation hygiene; the prose is correct.
- DRY analysis (`_camel_case` cross-folder extraction): defer-with-trigger restated verbatim from `rev-utils__strings.md`. Trigger: "the 0.0.8 cycle's `orders/` review closes; the cycle that closes `orders/` second owns the extraction." `orders/` is concurrent spec-028 Slice 3 maintainer work landing post-baseline (commit `b8fbd74` per `rev-utils__strings.md` Notes) and is NOT in the 0.0.7 review plan per `docs/review/review-0_0_7.md:1-99`.
- No GLOSSARY-only fix in scope. All seven exported public symbols correctly absent from `docs/GLOSSARY.md` per internal-mechanics-absence calibration. The forward-extension reference at `GLOSSARY.md:1171` to `utils/queryset.py` as `BETTER item 36` is the only `utils/`-relevant GLOSSARY content; it is correct prose and out of scope for this folder pass.
- Shadow files for `utils/__init__.py` and `utils/relations.py` regenerated this cycle (`python scripts/review_inspect.py … --output-dir docs/shadow` ran once for each); these are gitignored.
- Concurrent maintainer activity: working-tree carries 35+ modified/untracked entries (KANBAN.html / KANBAN.md regeneration; `kanban-app/` working files; `types/*.py` edits attributable to verified sibling cycles per the dirty-tree-from-verified-siblings calibration; spec-028 Slice 3 `orderset_class` landing files). Per `AGENTS.md` #33 and the "Concurrent maintainer work attribution" calibration: presumptively concurrent maintainer/dev work; left untouched.
- `uv.lock` unchanged.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits in scope — every Low is explicitly forward-looking and deferred until the corresponding trigger fires; the DRY analysis bullet is also defer-with-trigger gated on the 0.0.8 cycle. Each per-file artifact's docstring-level Lows already closed at `Status: verified` (L1 docstring fix in `rev-utils__relations.md` landed in this cycle's working tree at `django_strawberry_framework/utils/relations.py:54-61`).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no behaviour change, no public-API change, no consumer-visible surface change at folder scope. Citations: `AGENTS.md` #21 ("Do not update CHANGELOG.md unless explicitly instructed"); active plan `docs/review/review-0_0_7.md` is silent on changelog updates for per-file or folder review artifacts.

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit folder pass on the three-submodule `utils/` subpackage (`__init__.py` 32 lines + `relations.py` + `strings.py` + `typing.py`, 249 total source lines). Zero High / Medium with three forward-looking Lows all carrying verbatim "Defer until …" trigger phrasing:

- **L1 (trio-cut on submodule `__all__`):** folder-scope decision is do-not-act; restated trigger condition supersedes the three per-file phrasings — "Defer until either (a) the package adopts a uniform submodule `__all__` convention as a package-wide cleanup pass, OR (b) any utils submodule grows a fourth public symbol where the internal-helper / public-symbol split inside the submodule becomes load-bearing." Package-wide convention audit confirmed: submodule-level `__all__` is the exception (only `optimizer/extension.py`, `exceptions.py`, `list_field.py`, `sets_mixins.py` carry one); every submodule under `filters/`, `types/`, other `optimizer/`, and `testing/` lack one. Acting on `utils/*.py` would create a single-folder anomaly.
- **L2 (`unwrap_return_type` zero-current-production-consumer audit-trail at folder-scope `__init__.py`):** forwarded with same trigger as `rev-utils__typing.md::L5` verbatim — "version bumps to 0.0.9 without a non-test call site of `unwrap_return_type` landing in `django_strawberry_framework/`."
- **L3 (`queryset` future-extension framing missing `BETTER item 36` cross-reference tag):** forwarded with trigger "next time `utils/__init__.py` is edited for any reason." Pure citation hygiene per AGENTS.md #28 / #27 calibration.

All three sibling per-file artifacts confirmed `Status: verified` on disk (`rev-utils__relations.md`, `rev-utils__strings.md`, `rev-utils__typing.md`). DRY analysis "None" claim at folder scope grep-confirmed: each `utils/` submodule is a single-concern canonical-home extraction with zero within-folder cross-deps; the one cross-folder act-now-eligible DRY opportunity (`_camel_case` extraction) is defer-with-trigger restated verbatim from `rev-utils__strings.md` gated on the 0.0.8 cycle's `orders/` review.

### Shape #5 verification (5-check)
1. **Scoped diff against baseline (HEAD):** the wide `git diff --stat HEAD -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` is NOT empty (10 files / +141/-106) but every hunk attributes to closed sibling cycles per worker-3 memory entries — the only `utils/`-scope hunk is `utils/relations.py` (+9 docstring-only lines at `:54-61`) which is the verified output of `rev-utils__relations.md`'s Low #1 fix; remaining hunks (`optimizer/field_meta.py`, `types/{base,finalizer,relations,relay,resolvers}.py`, `docs/GLOSSARY.md`, `tests/types/{test_base,test_relay_interfaces}.py`) attribute to verified sibling cycles per memory entries under `## types/base.py`, `## types/finalizer.py`, `## types/relations.py`, `## types/relay.py`, `## types/resolvers.py`, `## types/ (folder pass)`. Same dirty-tree-from-verified-sibling pattern as `management/commands/`, `management/`, `optimizer/`, `testing/`, `utils/strings.py`, `utils/typing.py`. The folder pass's own "Files touched: None" claim holds; recorded attribution explicitly per the established pattern. ✓
2. **Boilerplate verbatim in all three Worker 2 sections:** Fix report (L91), Comment/docstring pass (L118), Changelog disposition (L124) — all open with "Filled by Worker 1 per no-source-edit cycle pattern". ✓
3. **Every Low has verbatim trigger phrasing; no GLOSSARY-only fix in scope:** L1 restated trigger ("Defer until either (a) … OR (b) …"), L2 verbatim from `rev-utils__typing.md::L5`, L3 explicit trigger ("next time `utils/__init__.py` is edited for any reason"). No GLOSSARY-only fix present. ✓
4. **Changelog `Not warranted` with both citations:** L124 cites both `AGENTS.md` #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND active plan silence at `docs/review/review-0_0_7.md`; `git diff -- CHANGELOG.md` is empty. ✓
5. **Ruff format-check + check pass:** `uv run ruff format --check .` → 213 files already formatted; `uv run ruff check .` → All checks passed!. ✓

### DRY findings disposition
Folder-scope DRY analysis is "None — every per-file artifact closed at folder-pass-relevant scope" with one cross-folder defer-with-trigger DRY opportunity (`_camel_case` extraction across `filters/inputs.py:783-789` and `orders/inputs.py:164-170` through new `utils/strings.py::camel_case`) restated verbatim from `rev-utils__strings.md::DRY analysis`. Trigger: "the 0.0.8 cycle's `orders/` review closes; the cycle that closes `orders/` second owns the extraction per the second-closing-folder calibration." `orders/` is concurrent spec-028 Slice 3 maintainer work landing post-baseline (commit `b8fbd74`) and is NOT in the 0.0.7 review plan per `docs/review/review-0_0_7.md`. The deferral is for cycle-boundary hygiene; the audit trail is preserved in `## What looks solid > ### DRY recap`.

### Temp test verification
- Temp test files used: none — shape #5 no-source-edit folder pass; verification is mechanical against existing pinning tests already cited in sibling artifacts (`tests/utils/test_relations.py`, `tests/utils/test_strings.py`, `tests/utils/test_typing.py`).
- Disposition: N/A.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `docs/review/review-0_0_7.md`.

---

## Iteration log

(none)
