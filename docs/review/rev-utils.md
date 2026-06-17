# Review: `django_strawberry_framework/utils/`

Status: verified

Folder pass over the shared-substrate package consumed by every other folder.
Covers `utils/__init__.py` (shadow
`docs/shadow/django_strawberry_framework__utils____init__.overview.md`) and reads
all 8 `verified` sibling artifacts: `rev-utils__connections.md`,
`rev-utils__input_values.md`, `rev-utils__inputs.md`, `rev-utils__permissions.md`,
`rev-utils__querysets.md`, `rev-utils__relations.md`, `rev-utils__strings.md`,
`rev-utils__typing.md`. No sibling forwarded a folder-scope concern.

## DRY analysis

- None — `utils/` is the package's consolidation substrate: every sibling *is* the
  single-source for one cross-subsystem contract (relations → relation-shape
  classification; strings → the GraphQL↔Django case boundary; typing → the three
  type-introspection helpers; connections → window-bounds + sidecar kwargs;
  inputs → the generated-input factory chokepoint; input_values → the neutral
  set-input traversal substrate; permissions → the active-input permission walker;
  querysets → the `DjangoType.get_queryset` visibility contract). The per-file
  artifacts already established DRY=None for each, and the folder-pass
  repeated-literal check confirms no literal is shared across two+ siblings —
  each file's repeated literals stay file-local and intentional (inputs'
  collision-message tails diagnose two distinct failure modes; relations'
  `reverse_many_to_one`/`forward_single`/`auto_created` are the enumerated
  `RelationKind` vocabulary, defined once each). Folding any sibling into another
  re-entangles independently-evolvable contracts and is net-negative.

## High:

None.

## Medium:

None.

## Low:

None at folder scope. Three submodule-direct-vs-package-root `__all__` asymmetries
were raised by siblings as forward-looking Lows and are confirmed coherent at folder
scope (not folder defects):

- `unwrap_return_type` (`rev-utils__typing.md`) — in `__all__` and re-exported at
  package root but has zero first-party callers (orphaned by commit `32b7e033`,
  which moved the optimizer onto `unwrap_graphql_type`). Public-but-orphaned,
  correct + tested, trigger-gated in the typing artifact. Not a folder finding:
  the export exists and points at a real, correct symbol; coherence of the surface
  is intact, only the consumer is absent.
- `instance_accessor` (`rev-utils__relations.md`) — NOT in `__all__`, imported
  submodule-direct (`..utils.relations`) by 3 consumers
  (`types/finalizer.py`, `types/resolvers.py`, `optimizer/walker.py`). Consistent
  across all call sites and the package docstring's `relations` bullet.
- `is_async_callable` (`rev-utils__typing.md`) — NOT in `__all__`, imported
  submodule-direct by 3 consumers (`connection.py`, `list_field.py`,
  `types/base.py`). Consistent across all call sites; the docstring names it
  descriptively, not as a re-export promise.

These three are forwarded to the project pass for one coherent disposition rather
than re-litigated here; see `rev-django_strawberry_framework.md`. Submodule-direct
import is an accepted pattern in this package, and the per-file trigger conditions
(a consumer importing the symbol via the package root, or an API-trim pass) remain
the right gates.

## What looks solid

### DRY recap

- **Existing patterns reused.** `utils/__init__.py` re-exports exactly the seven
  public symbols from their owning submodules — `RelationKind` /
  `is_many_side_relation_kind` / `relation_kind` (`relations.py:7,80,35`),
  `pascal_case` / `snake_case` (`strings.py:55,22`), `unwrap_graphql_type` /
  `unwrap_return_type` (`typing.py:57,85`) — no logic, pure surface aggregation.
  `permissions.py` reuses the `input_values` traversal substrate
  (`permissions.py:35` `from .input_values import ...`), the only intra-utils
  load-time sibling import besides `__init__`'s.
- **New helpers considered.** None at folder scope. The siblings carry trigger-gated
  defer-with-trigger DRY candidates entirely *within* their own files
  (inputs' 8-kwarg `clear` surface → `ClearSpec` at a 3rd family; resolvers-style
  twins counted folder-wide already in `types/`). No cross-utils helper is
  warranted: the only shared seam, set-input traversal, already lives once in
  `input_values.py`.
- **Duplication risk in the current folder.** The cross-sibling repeated-literal
  scan (shadow "Repeated string literals" sections) shows zero literal shared
  across two+ files. inputs' `". Rename one"` / `"...unique."` tails and relations'
  `RelationKind` member strings are each file-local, intentional, and already
  cleared in the per-file artifacts.

### Other positives

- **Import direction is strictly inward.** Zero `utils → filters/orders/optimizer/`
  `types/management/testing` edges (grep over all `utils/*.py` load-time and
  in-function imports — the only non-`__init__` sibling import is
  `permissions.py → input_values`, and the apparent in-function hits are docstring
  prose, not statements). `utils/` imports only stdlib, `typing`, Django ORM
  (in `querysets.py`), and `..exceptions` / `..sets_mixins` from the package root —
  never a sibling top-level subsystem. No cycle: `input_values` (the one imported
  sibling) imports no utils sibling, so the intra-folder DAG is acyclic.
- **`__all__` surface is internally coherent.** All 7 names in
  `utils/__init__.py.__all__` resolve to a real symbol in their owning submodule
  and are intended public. The package docstring (`__init__.py:1-27`) describes the
  submodule map accurately. Symbols left out of `__all__`
  (`instance_accessor`, `is_async_callable`, and the deeper helpers in
  inputs/input_values/permissions/querysets/connections) are consumed
  submodule-direct — the documented, consistent pattern in this package.
- **`verbatim_path` promotion is coherent folder-wide.** The prior-cycle
  `_verbatim_path` → public `verbatim_path` promotion is clean: defined at
  `permissions.py:149`, listed in `__all__` (`permissions.py:70`), used internally
  (`permissions.py:249` `fallback_path=verbatim_path`) and by one consumer
  (`orders/sets.py:47,362`). No orphan `_verbatim_path` remains anywhere in source,
  tests, or examples.
- **Each sibling reached `verified` independently.** All 8 per-file cycles closed
  clean; none surfaced a High/Medium, and the consolidation-point factoring held up
  branch-by-branch in every per-file review (SliceMetadata parity in connections,
  sync/async parity in querysets, identity-based collision in inputs, exhaustive
  classification in relations/input_values/permissions, idempotency invariant in
  strings, bounded-recursion in typing).

### Summary

`utils/` is the package's shared-substrate folder and reviews as a textbook
consolidation point: eight orthogonal single-source contracts, each already cleared
DRY=None in its per-file pass, with no cross-file literal or helper duplication at
folder scope. The three `__all__` asymmetries the siblings flagged
(`unwrap_return_type` in `__all__` but orphaned; `instance_accessor` and
`is_async_callable` out of `__all__` but submodule-direct-imported) are internally
consistent — every export points at a real intended-public symbol, every omitted
symbol is imported the documented submodule-direct way, and the package docstring
agrees with both. The `verbatim_path` promotion is coherent with no orphan left
behind. Import direction is strictly inward with an acyclic intra-folder DAG. No
folder-level finding; the three asymmetries are forwarded to
`rev-django_strawberry_framework.md` for one project-scope disposition. No-findings
folder pass, zero source edits → shape #3 → #5.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files unchanged.
- `uv run ruff check --fix .` — all checks passed.

### Notes for Worker 3
- No-findings folder pass. High/Medium/Low all `None.` at folder scope.
- Three forward-looking Lows are NOT folder defects — each was raised and
  trigger-gated in a sibling per-file artifact (`unwrap_return_type` orphan +
  `is_async_callable` asymmetry in `rev-utils__typing.md`; `instance_accessor`
  asymmetry in `rev-utils__relations.md`) and is confirmed coherent at folder
  scope. They are forwarded to `rev-django_strawberry_framework.md` for one
  project-scope disposition of the `__all__` surface, not actioned here.
- Folder-level checks all pass: (1) `__all__` surface coherent — all 7 exports
  resolve to real intended-public symbols; (2) `verbatim_path` promotion coherent,
  no orphan `_verbatim_path`; (3) import direction strictly inward, acyclic
  intra-folder DAG.
- No GLOSSARY-only fix in scope.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no-source-edit folder pass, no behavior change. Per AGENTS.md
("Do not update CHANGELOG.md unless explicitly instructed") and the active plan
(`docs/review/review-0_0_10.md`), which is silent on any changelog entry for this
folder pass.

---

## Verification (Worker 3)

Terminal-verify, folder pass (shape #5, no-findings). All load-bearing claims
re-derived from LIVE source, not trusted from the artifact prose.

### Logic verification outcome

H/M/L all `None.` at folder scope — nothing to address. The three submodule-direct
asymmetries the siblings flagged as forward-looking Lows are confirmed coherent at
folder scope and correctly forwarded to `rev-django_strawberry_framework.md` (not
folder act-now):

- `__all__` surface (7 entries) all resolve to real public symbols in their owning
  submodules: `relations.py` `RelationKind` (TypeAlias :7), `relation_kind` (:35),
  `is_many_side_relation_kind` (:80); `strings.py` `snake_case` (:22),
  `pascal_case` (:55); `typing.py` `unwrap_graphql_type` (:57),
  `unwrap_return_type` (:85). No dangling export.
- Submodule-direct pattern is genuine, not accidental drift. `instance_accessor`
  (NOT in `__all__`) imported `from ..utils.relations` by FOUR consumers
  (`types/finalizer.py:65`, `types/resolvers.py:50`, `optimizer/walker.py:22`,
  `optimizer/field_meta.py:26` — artifact said 3; the 4th strengthens coherence,
  does not contradict it). `is_async_callable` (NOT in `__all__`) imported
  `from .utils.typing` by THREE consumers (`connection.py:83`, `list_field.py:27`,
  `types/base.py:57`). Both appear in `utils/__init__.py` only as descriptive
  docstring prose (:11), never as `__all__` entries — consistent with the
  documented submodule-direct convention.
- `unwrap_return_type` orphan confirmed: repo+examples grep returns only the def,
  the `__init__` re-export (:31) + `__all__` (:40) + docstring (:11), and its
  test (`tests/utils/test_typing.py`). Zero first-party callers. PUBLIC (in
  `__all__`) → forward-defer is correct, not act-now removal (dropping from
  `__all__` is a breaking change to defer). Per-file trigger gates remain the
  right disposition point.

### DRY findings disposition

DRY=None held: each sibling is the single-source for one orthogonal cross-subsystem
contract. No cross-file literal or helper shared across two+ siblings; the only
intra-utils load-time sibling edge is `permissions.py:35 from .input_values import`,
and `input_values` imports no utils sibling → acyclic intra-folder DAG. Folding any
pair re-entangles independently-evolvable contracts. Carried forward as None.

### Import-direction verdict (load-bearing)

STRICTLY INWARD, confirmed by grep over all `utils/*.py`:
`grep -rnE "from \.\.(filters|orders|optimizer|types|management|testing)"` over
`utils/` returns ZERO — no sibling-subsystem back-edge, so no cycle risk. The only
package-root `..` imports are `..exceptions` (querysets.py:32, permissions.py:34,
inputs.py:35); the two `..utils.permissions` hits (input_values.py:64,
permissions.py:59) are docstring/comment prose, not import statements. Acyclic DAG
intact.

### verbatim_path coherence

One `def verbatim_path` (permissions.py:149), in `__all__` (:70), used internally
(`fallback_path=verbatim_path` :248) and by consumer `orders/sets.py`. Repo-wide
`grep _verbatim_path` over source/tests/examples = NONE — no orphan remains.

### No new edits this cycle

`git diff HEAD -- django_strawberry_framework/utils/` shows ONLY the 14-line
`verbatim_path` promotion (`_verbatim_path` → public, `__all__` entry, two
call-site repoints) — the reviewed prior-cycle state already accepted in the
`utils/permissions.py` per-file cycle, NOT a new edit. `git diff HEAD -- CHANGELOG.md`
and `docs/GLOSSARY.md` both empty.

### Shape #5 / changelog / ruff

(a) per-item zero-edit proof = only the prior-cycle verbatim_path hunk, nothing new;
(b) each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.`;
(c) every Low forwarded (no GLOSSARY-only fix in scope); (d) changelog `Not warranted`
cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND
active-plan silence, `git diff -- CHANGELOG.md` empty; (e) `uv run ruff format --check`
+ `ruff check` over `utils/` both pass (9 files already formatted, all checks passed).

### Temp test verification

None — no behavior claim required a temp test (no-findings folder pass; the
load-bearing claims are grep/source-decidable).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
`utils/` folder-pass checklist box in `docs/review/review-0_0_10.md`.
