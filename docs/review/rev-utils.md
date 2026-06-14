# Review: `django_strawberry_framework/utils/`

Status: verified

Folder pass over `django_strawberry_framework/utils/` — the cross-cutting substrate every
subsystem consumes. Supersedes the prior on-disk 0.0.7 artifact (`Status: verified`, refs
`review-0_0_7.md`, knew only the three submodules `relations`/`strings`/`typing` and predated the
0.0.9 substrate-consolidation files `input_values`/`inputs`/`permissions`/`querysets`/
`connections`) wholesale. Reviewed against all 8 verified sibling artifacts (`rev-utils__{connections,
input_values,inputs,permissions,querysets,relations,strings,typing}.md`), the 8 submodule sources +
`utils/__init__.py`, and the refreshed shadow overviews
(`docs/shadow/django_strawberry_framework__utils__*.overview.md`, including `__utils____init__`).

This is a **no-source-edit folder pass** (REVIEW.md shape #5): zero High, zero behaviour-changing
Medium, every Low forward-looking-with-trigger or recorded-on-inspection, and the two forwarded
`rev-utils__typing.md` items (L4 submodule `__all__` gap, L5 `__init__` docstring/`__all__`
asymmetry) adjudicate to NO act-now folder-level edit (see L1/L2 below). No GLOSSARY-only fix in
scope.

## DRY analysis

- None — `utils/` is the realized DRY substrate, not a candidate for further consolidation. Five
  of the eight submodules (`input_values.py`, `inputs.py`, `permissions.py`, `querysets.py`,
  `connections.py`) are each themselves a "this module IS the consolidation" file landed by the
  0.0.9 DRY pass (`docs/feedback.md` Major 1/3/4), single-siting a pattern the filter / order
  families previously spelled inline. The folder-level cross-sibling repeated-literal sweep
  (shadow "Repeated string literals" across all 8 + `__init__`) finds **no literal shared by
  two-or-more files**: the only repeats are intra-file and already-adjudicated sibling design —
  `inputs.py` (`3x description`, `2x __annotations__`, the two collision-message fragments
  `". Rename one"` / `"so its class-derived input type name is unique."`) and `relations.py`
  (`3x reverse_many_to_one`, `2x reverse_one_to_one`/`forward_single`/`auto_created` — the
  relation-kind token vocabulary). No cross-file duplication to lift. Each sibling artifact's
  defer-with-trigger DRY bullets (the combined `unwrap(deep=)` dispatcher, the
  `CONNECTION_SIDECAR_KWARGS` presence-loop, the `check_…_permission` name-formula extraction, the
  paired postgres/sentinel folds) stay deferred at folder scope — none of their triggers fire
  within `utils/`.

## High:

None.

## Medium:

None.

## Low:

### L1 — submodule `__all__` present on exactly one of eight submodules (`permissions.py`); folder-coordinated forward, stays deferred

`rev-utils__typing.md` L4 forwarded the "submodule `__all__` gap" here for a folder-level
act-now-vs-defer decision. Confirmed at source: of the eight `utils/` submodules, **only
`permissions.py` carries a module-level `__all__`** (`permissions.py::__all__`, naming its seven
public funcs including the `iter_input_items` legacy re-export); `connections.py`,
`input_values.py`, `inputs.py`, `querysets.py`, `relations.py`, `strings.py`, and `typing.py`
all have none.

This is a real one-off inconsistency, but it is **not** an act-now folder edit, for two reasons:

1. The only consumer path a submodule `__all__` governs is `from …utils.<submodule> import *`,
   which is not a documented entrypoint anywhere in the package — every real consumer imports
   named symbols by explicit submodule path (verified: all `snake_case`/`relation_kind`/
   `unwrap_graphql_type`/`is_async_callable` consumers use `from ..utils.<sub> import <name>`,
   never a star-import). Adding seven `__all__` tuples buys no consumer-visible behaviour.
2. `permissions.py`'s `__all__` is load-bearing for a *different* reason than star-import
   curation: it advertises the legacy `iter_input_items` re-export (homed at
   `input_values.py::iter_input_items`, re-exported through `permissions.py` for the documented
   `from ..utils.permissions import iter_input_items` back-compat path) as a deliberate public
   surface of that module. It is not evidence the other seven *should* grow one — it is evidence
   `permissions.py` had a concrete re-export to advertise and the others do not.

Defer with the trigger quoted from `rev-utils__typing.md` L4: **"sibling `utils/` submodules grow
an `__all__`"** — i.e. land a uniform `__all__` across all eight submodules *only* when a second
submodule acquires a concrete reason to advertise a curated public surface (a star-import
entrypoint or a legacy re-export like `permissions.py`'s). Until then the single `permissions.py`
`__all__` is justified by its re-export and the trio-of-defers (typing/relations/strings) stays
deferred. Non-contract (GLOSSARY carries none of these symbols).

### L2 — `utils/__init__.py` docstring lists `is_async_callable` alongside the re-exported unwrap pair; reads as a re-export but is submodule-only — resolved-on-inspection, no edit

`rev-utils__typing.md` L5 forwarded the "`__init__` docstring/`__all__` asymmetry" here.
Re-confirmed at source (`utils/__init__.py`):

- The module docstring (`utils/__init__.py #"plus ``is_async_callable``"`) describes the `typing`
  submodule as: *type unwrapping (`unwrap_graphql_type`, `unwrap_return_type`) plus
  `is_async_callable`.*
- The re-export block (`from .typing import unwrap_graphql_type, unwrap_return_type`) and the
  `__all__` tuple export **only** the two unwrap helpers; `is_async_callable` is reached by all
  three consumers (`connection.py`, `list_field.py`, `types/base.py`) via the submodule path
  `…utils.typing import is_async_callable`.

Adjudication: **no edit warranted.** Read precisely, the docstring is a per-submodule **content
inventory** ("the `typing` submodule contains unwrap_graphql_type, unwrap_return_type, plus
is_async_callable"), and it is *accurate* as such — all three symbols genuinely live in
`typing.py`. It is NOT a re-export claim; the surrounding bullets (`relations` lists three
symbols of which all three ARE re-exported, but `querysets` lists `SyncMisuseError` /
`initial_queryset` / `apply_type_visibility_*` — none re-exported via `__init__`; `inputs` /
`permissions` describe submodule contents wholly absent from `__init__.__all__`) follow the same
"what's in the submodule" convention, so the docstring is internally consistent. The `__all__`
tuple is the separate, correct, curated re-export surface. The two serve different purposes and
both are correct.

The perception risk that seeded `rev-utils__typing.md` L5 (the docstring sitting directly above
`__all__` could read as a re-export promise for all three) is real but does not rise to a
required edit: the `querysets`/`inputs`/`permissions` bullets in the same docstring all describe
submodule contents deliberately NOT in `__init__.__all__`, so a reader who treats the docstring as
a re-export manifest would already be misreading every other bullet — the convention is
unambiguous in aggregate. Recorded resolved-on-inspection; non-contract. **If** a future cycle
wants belt-and-suspenders clarity, the minimal phrasing notes the re-export surface separately from
the per-submodule inventory — but that is polish, not a defect, and is explicitly NOT actioned here
(a docstring edit would push this off shape #5 with no correctness or contract gain).

## What looks solid

### DRY recap

- **Existing patterns reused.** `utils/` is the canonical home for every cross-cutting helper and
  every subsystem imports back rather than re-spelling: relation-shape classification
  (`relations.py`, consumed by `optimizer/{walker,field_meta,plans}.py`, `orders/sets.py`,
  `types/{relations,resolvers}.py`); case conversion (`strings.py`, consumed by
  `types/{base,finalizer,converters}.py`, `optimizer/walker.py`, `sets_mixins.py`,
  `management/commands/inspect_django_type.py`); type unwrapping + the async-callable predicate
  (`typing.py`, consumed by `optimizer/extension.py`, `connection.py`, `list_field.py`,
  `types/base.py`); the cursor-parity window + sidecar contract (`connections.py`, consumed by
  `optimizer/{walker,plans}.py` + `connection.py`); the generated-input ledger (`inputs.py`) and
  query-source/visibility contract (`querysets.py`) both consumed by the filter + order families;
  the neutral set-input traversal (`input_values.py`) consumed by both normalizers AND
  `permissions.py`; the active-input permission gate (`permissions.py`) consumed by
  `filters/sets.py` + `orders/sets.py` via thin delegates.
- **New helpers considered.** None warranted at folder scope. The combined `unwrap(deep=)`
  dispatcher (`rev-utils__typing.md`), the `CONNECTION_SIDECAR_KWARGS` presence-loop
  (`rev-utils__connections.md`), and the `check_…_permission` name-formula extraction
  (`rev-utils__permissions.md`) are each deferred-with-trigger in their owning artifact, and none
  of their triggers fire within `utils/`.
- **Duplication risk in the current folder.** None cross-file. Intra-file repeats
  (`inputs.py` collision-message fragments + `description`/`__annotations__`; `relations.py`
  relation-kind tokens) are single-source-of-truth-within-their-file design, adjudicated in the
  per-file artifacts. No literal is shared by two-or-more `utils/` files.

### Other positives

- **One-way leaf direction — VERIFIED CLEAN.** `utils/` imports nothing from `filters/`,
  `orders/`, `optimizer/`, or `types/` — not at module load, not under `TYPE_CHECKING`, not via
  in-function lazy reads. Full grep of the four sibling-subsystem names across all 8 submodules
  returns exactly one match, and it is a *comment* (`permissions.py #"from ..utils.permissions
  import iter_input_items"` naming its consumers), not an import. The only first-party imports
  anywhere in `utils/` are `..exceptions` (`ConfigurationError`, in `inputs`/`permissions`/
  `querysets`) and one intra-folder edge (`permissions.py` → `input_values.py`, the consolidation
  substrate depending on the neutral traversal it builds on — correct direction). External
  dependencies are stdlib, `strawberry` (`connections`/`inputs`), and `django` (`querysets`/
  `permissions`). `utils/` is a true acyclic leaf; the stated reason `connections.py` exists
  (cycle-safety so both the walker and the connection field can import it) holds folder-wide.
- **Substrate-consolidation set is coherent.** The 0.0.9 DRY files form a clean two-tier
  substrate: `input_values.py` is the neutral set-input traversal primitive (dict-vs-dataclass
  walk, `None`/`UNSET` active rule, leaf/related/logic classification); `permissions.py` builds
  the active-input permission gate ON TOP of it (imports `input_values`, threads
  `iter_active_fields`); `inputs.py` (generated-input ledger), `querysets.py` (query-source +
  visibility), and `connections.py` (cursor-parity window) are the three independent
  consolidation targets each consumed by both the filter and order families. Each is the single
  site for what every per-file artifact verified the filter/order families previously duplicated.
  No two consolidation files overlap in responsibility.
- **Error-handling / sentinel patterns are consistent and intentional.** `ConfigurationError`
  (build/config faults — `inputs`/`permissions`/`querysets`) vs `SyncMisuseError`
  (`querysets.py`, the dual-inherit ConfigurationError+RuntimeError sync-misuse signal) vs the
  control-flow `UnwindowableConnection` sentinel (`connections.py`, deliberately NOT a
  `…Error`, `# noqa: N818` justified inline) form a clear three-way split by blast radius:
  consumer-config faults raise the family error, the visibility-misuse case raises the
  dual-inherit error, and the internal plan-time fallback raises the bare-Exception control-flow
  sentinel the walker catches. No drift across the folder.
- **Per-file verification carries forward clean.** All 8 siblings are `Status: verified`:
  `connections.py` (the one High this folder ever had — `after`+`last` `pageInfo` parity — was
  fixed at root cause and verified, with the live wire-parity pin); `querysets.py` (one GLOSSARY
  Medium fixed); `permissions.py` (security-adjacent gate-dispatch verified — deny gates fire for
  exactly supplied active inputs, parent/child double-dispatch correct-by-construction); the
  remaining five reviewed clean with forward-looking Lows only.
- **GLOSSARY: no folder-level drift.** Per-file checks recorded zero per-symbol hits for the
  internal-mechanics submodules (`input_values`/`inputs`/`connections`/`relations`/`strings`/
  `typing` — correct, internal substrate gets no entry) and accurate prose for the
  public-contract surfaces (`querysets.py::SyncMisuseError` Medium already fixed via the sibling
  cycle). No new folder-pass GLOSSARY finding.

### Summary

`utils/` is a coherent, correctly-factored cross-cutting leaf: it imports nothing from the four
sibling subsystems (verified — the single grep hit is a comment, not an import), every consumer
imports helpers back by explicit submodule path, and the 0.0.9 substrate-consolidation files
(`input_values`/`permissions`/`inputs`/`querysets`/`connections`) form a clean two-tier set with
no overlapping responsibility and no cross-file repeated literal. All 8 siblings are verified; the
folder carried exactly one historical High (`connections.py` `after`+`last`, fixed at root cause)
and no open Medium. The two forwarded `rev-utils__typing.md` items adjudicate to NO act-now edit:
L4 (submodule `__all__` gap) stays a folder-coordinated defer — only `permissions.py` warrants its
`__all__` today (it advertises the `iter_input_items` legacy re-export), and star-imports are not
a documented entrypoint; L5 (`__init__` docstring/`__all__` asymmetry) is resolved-on-inspection —
the docstring is an accurate per-submodule content inventory, not a re-export manifest, internally
consistent with every other bullet. One cross-folder concern is forwarded to the project pass: the
`orders/sets.py::OrderSet.check_permissions` read of a never-written `_input_value`
(`orders/sets.py #"getattr(self, "_input_value", None)"`) makes the bound-method order-side
permission check an effective no-op — surfaced while reading the shared `permissions.py` gate, but
owned by `orders/sets.py` / the project pass, not this folder. No-source-edit folder pass: ruff
clean, bare `fix-implemented`.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/utils/` — `9 files already formatted`
  (COM812 formatter-conflict warning is standing/expected).
- `uv run ruff check django_strawberry_framework/utils/` — `All checks passed!`.

### Notes for Worker 3
- Per-Low dispositions: **L1** (submodule `__all__` gap) forward-looking, deferred with verbatim
  trigger "sibling `utils/` submodules grow an `__all__`" — adjudicated act-now=NO at folder scope
  (only `permissions.py` warrants its `__all__` today, for its `iter_input_items` re-export;
  star-imports are not a documented entrypoint). **L2** (`__init__` docstring/`__all__` asymmetry,
  forwarded from `rev-utils__typing.md` L5) resolved-on-inspection: the docstring is an accurate
  per-submodule content inventory, not a re-export manifest — no edit. Both are non-contract
  (GLOSSARY carries none of the symbols).
- Forwarded L4/L5 from `rev-utils__typing.md` are BOTH captured above and BOTH adjudicate to no
  act-now folder edit (forward/stay-deferred, not under-review).
- One-way leaf direction verified clean (zero back-edges to filters/orders/optimizer/types; the
  single grep hit is a comment in `permissions.py`, not an import).
- Cross-folder forward to the project pass `rev-django_strawberry_framework.md`: the never-written
  `_input_value` read at `orders/sets.py::OrderSet.check_permissions` (effective no-op order-side
  bound-method permission check). Owned by `orders/sets.py` / project pass, NOT this folder.
- No GLOSSARY-only fix in scope.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit folder pass (shape #5), independently re-confirmed at source:

- **Baseline / files-touched.** `git diff --stat 0872a20…26 -- django_strawberry_framework/utils/`
  shows ONE dirty path: `connections.py` (+40). That hunk attributes to the closed sibling cycle
  `rev-utils__connections.md` (`Status: verified`, `[x]` at `review-0_0_9.md:119`). All other 7
  submodules + `__init__.py` byte-empty vs baseline. The folder pass's own "Files touched: None"
  holds.
- **One-way leaf property — VERIFIED CLEAN.** `grep -rnE "^\s*(from|import)"` over all 9 files:
  the only first-party imports are `..exceptions` (`inputs`/`permissions`/`querysets`) and one
  intra-folder edge `permissions.py` → `.input_values` (correct direction). ZERO real import lines
  reference `filters`/`orders`/`optimizer`/`..types`/`.field_meta`. Every `filters|orders|optimizer`
  grep hit across `utils/*.py` is docstring/comment prose, not an import statement. `utils/` is a
  true acyclic leaf.
- **L1 (submodule `__all__` gap) — accept defer.** `grep -rn "^__all__" utils/` returns exactly two:
  `permissions.py:47` and `__init__.py:33`. So `permissions.py` is the ONLY submodule with an
  `__all__`, and it is justified — it advertises the `iter_input_items` legacy re-export (homed at
  `input_values.py`, re-exported through `permissions.py` for the documented
  `from ..utils.permissions import iter_input_items` back-compat path, with the rationale comment at
  `permissions.py:43-46`). No act-now folder edit; trigger "sibling `utils/` submodules grow an
  `__all__`" correctly carried.
- **L2 (`__init__` docstring/`__all__` asymmetry) — accept resolved-on-inspection.** Read at source:
  the docstring (`__init__.py:10-11`) lists `is_async_callable` alongside the unwrap pair as a
  per-submodule **content inventory** of `typing` (all three genuinely live in `typing.py`); the
  `__all__` tuple (`__init__.py:33-41`) re-exports ONLY `unwrap_graphql_type`/`unwrap_return_type`.
  The `querysets` bullet (`:21-23`) lists `SyncMisuseError`/`initial_queryset`/`apply_type_visibility_*`
  — none re-exported — confirming the docstring is uniformly a content inventory, NOT a re-export
  manifest. Accurate as-is; no edit warranted (a docstring edit would push off shape #5 with no
  contract gain).
- **`_input_value` dead-code forward — RECORDED, not dropped.** `grep -rn "_input_value\s*="` over
  `django_strawberry_framework/ tests/ examples/` returns exactly ONE writer,
  `tests/orders/test_sets.py:464` (test-only); ZERO production writers. The read at
  `orders/sets.py:460` is `getattr(self, "_input_value", None)` → always `None` in prod → effective
  no-op bound-method gate. Classified DEAD-CODE LOW (the live gate fires via the classmethod path
  `apply_sync:566`/`apply_async:605` `cls._run_permission_checks(input_value, request)`). The forward
  is recorded in the closed sibling `rev-utils__permissions.md` (full classification + 3-part repro,
  lines 86-114) AND re-surfaced in this artifact's Summary + Notes for Worker 3, with a spawn_task
  chip raised. Destination project artifact `rev-django_strawberry_framework.md` is `Status: verified`
  but its plan box (`review-0_0_9.md:128`) is still `- [ ]` — the project pass has not run; this is the
  normal supersede-on-unchecked-box pattern, NOT a reject. The forward survives in the contract input
  the project pass reads.

### DRY findings disposition
No cross-file repeated-literal missed: confirmed every `filters|orders|optimizer` token in
`utils/*.py` is comment/docstring text, and the only literal repeats are intra-file
(`inputs.py` collision-message fragments + `description`/`__annotations__`; `relations.py`
relation-kind tokens) — single-source-within-file design adjudicated in the per-file artifacts. The
sibling defer-with-trigger DRY bullets (`unwrap(deep=)` dispatcher, `CONNECTION_SIDECAR_KWARGS`
loop, `check_…_permission` name-formula) stay deferred — none of their triggers fire within `utils/`.

### Temp test verification
- None. Verification was grep/read-only over source + closed sibling artifacts; no behavior probe
  needed for a no-source-edit folder pass whose 8 siblings are all `Status: verified`.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the folder-pass checklist
  box. CHANGELOG diff empty (Not warranted, both citations present); ruff format-check + check pass
  on `utils/` (COM812 formatter notice standing/expected).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits in scope —
L2 is resolved-on-inspection (the `__init__` docstring is accurate as a content inventory), and
no other Low calls for a comment edit at folder scope.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no behaviour change, no
public-API change, no consumer-visible surface change (folder pass with zero source edits).
Citations: `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed"); the active
review plan (`docs/review/review-0_0_9.md`) is silent on changelog updates for review artifacts,
and a folder pass is never the authorising scope.

---

## Iteration log

_None yet._
