# Build: Cross-slice integration pass — optimizer_hardening / 0.0.10 (035)

Spec reference: `docs/spec-035-optimizer_hardening-0_0_10.md`
Build plan: `docs/builder/build-035-optimizer_hardening-0_0_10.md`
Status: final-accepted

Worker 1 cross-slice integration pass over the four in-spec slices (all `final-accepted`):
Slice 1 (G1 — evaluated-queryset guard, procedural closure / shipped `d1dea2fd`), Slice 2 (G2 —
operation-type `.only()` gating + Decision 5 FK-id-elision loaded-check; the only real code this
cycle), Slice 3 (G3 — fragment narrowing, deferred, no code), Slice 4 (doc + DB wrap, no `.py`
logic).

This pass records findings only. It does NOT edit source/tests, the build plan, or commit.

---

## Pre-steps (BUILD.md "Cross-slice integration pass", 5 required)

### Pre-step 1 — every prior `bld-slice-*.md` read, in slice order

Required context, no "as needed". All four read end-to-end:

- `docs/builder/bld-slice-1-g1_evaluated_queryset_guard.md` — `final-accepted`. Procedural closure;
  G1 shipped in `d1dea2fd` (the `getattr(result, "_result_cache", None) is not None` early-return in
  `extension.py::DjangoOptimizerExtension._optimize`, after the `normalize_query_source` coercion +
  `is_queryset` gate, before the `apply_to` tail). Four tests in `tests/optimizer/test_extension.py`.
- `docs/builder/bld-slice-2-g2_only_operation_gating.md` — `final-accepted`. The single derived
  `enable_only` bool threaded through the four projection writers in `walker.py`; the Decision 5
  loaded-check (`_fk_attname_is_deferred` + `_FK_ELISION_UNSAFE`) and the `force_unplanned` strictness
  bypass in `resolvers.py`. Full test coverage across `test_walker.py` / `test_extension.py` /
  `test_resolvers.py`. One spec edit (test rerouting) recorded.
- `docs/builder/bld-slice-3-g3_fragment_narrowing.md` — `final-accepted`. Procedural closure;
  deferred, no runtime code. Verified `selections.py::included_field_selections` still inlines
  unconditionally (no `classifier` / `fragments_only`); three `# TODO(spec-035 Slice 3)` anchors
  intact; carry-forward R1–R3 preserved in the spec.
- `docs/builder/bld-slice-4-doc_wrap.md` — `final-accepted`. Doc + DB wrap (GLOSSARY G1+G2 bodies,
  Strictness G3-deferral pointer, README/docs-README, CHANGELOG `[Unreleased]` `### Changed`/
  `### Fixed`, KANBAN `DONE-035-0.0.10`). No `.py` logic, no version bump.

### Pre-step 2 — static inspection helper coverage confirmed for every touched Python file

The build touched three `.py` files with review-worthy logic. The helper was run (with
`--output-dir docs/shadow`) this pass to refresh the shadow overviews:

- `django_strawberry_framework/optimizer/walker.py` — refreshed (`...optimizer__walker.overview.md`).
  Worker 3 ran it during the Slice 2 review (recorded in `bld-slice-2`). **Has G2 logic.**
- `django_strawberry_framework/types/resolvers.py` — refreshed (`...types__resolvers.overview.md`).
  Worker 3 ran it during the Slice 2 review. **Has Decision 5 logic.**
- `django_strawberry_framework/optimizer/extension.py` — refreshed (`...optimizer__extension.overview.md`)
  for the G1 cross-check. G1 is shipped/committed (`d1dea2fd`); not in the uncommitted tree.

No file with review-worthy logic was skipped. Slice 3 added no code (verified). Slice 4 added no
`.py` logic — Worker 3 correctly recorded the helper as skipped for it (doc + DB only).

### Pre-step 3 — "Repeated string literals" compared across shadow overviews (cross-slice DRY)

Per-file executable repeated string literals (docstrings excluded by the helper):

| File | Repeated literals (count) |
| --- | --- |
| `optimizer/walker.py` | `arguments` (5), `prefetch` (3), `related_model` (3), `operation` (2), `_optimizer_runtime_prefixes` (2), `target_field` (2), `selections` (2) |
| `types/resolvers.py` | `__dict__` (2) |
| `optimizer/extension.py` | (none surfaced — 1 repeated literal, below the cross-file signal) |

**A literal appearing in 2+ files is the cross-slice DRY signal. Verdict: NONE.** Cross-checked the
two literals the build introduced:

- **`"operation"` (walker.py, 2x).** Both occurrences are intra-line, inside the single new helper
  `walker.py::_enable_only_for_operation` — `operation = getattr(getattr(info, "operation", None),
  "operation", None)`. It is the attribute-chain read of `info.operation.operation`, in ONE place.
  Confirmed by grep that `extension.py` reads the same chain via **direct attribute access**
  (`extension.py::_build_cache_key #"operation = info.operation"`), NOT a string literal — so
  `"operation"` does NOT appear as an executable literal in extension.py. No cross-file duplication.
- **`"__dict__"` (resolvers.py, 2x).** Both inside `resolvers.py` — `_fk_attname_is_deferred` (the
  new Decision 5 loaded-check) and the pre-existing `_will_lazy_load_single`. This is the deliberate,
  pre-existing defensive-loaded-check idiom (`field_name in getattr(root, "__dict__", {})`); Worker 3
  flagged it in Slice 2 as established idiom, not new duplication, and the new check is a deliberate
  variant keyed on the FK *column attname* vs the relation *field name*. `"__dict__"` does NOT appear
  as a literal in walker.py or extension.py. No cross-file duplication.

The pre-existing walker.py literals (`arguments`, `prefetch`, `related_model`, etc.) are untouched by
this build and are confined to walker.py. No new cross-file repeated literal, key, or tuple shape.

### Pre-step 4 — "Imports" compared across shadow overviews (one-way dependency direction)

The documented boundary: `optimizer/` is the lower layer; `types/` may depend on `optimizer/`, never
the reverse. Walked the Imports section of all three overviews:

- **`optimizer/walker.py`** imports only `..exceptions`, `..registry`, `..utils.*`, and sibling
  `optimizer/` modules (`. import logger`, `.hints`, `.plans`, `.selections`) — plus one deferred
  local import `from ..types.definition import origin_has_custom_id_resolver` (line 919, inside a
  function body). This `types/` import is **pre-existing** (not introduced by G2) and is a
  function-local lazy import used only for the custom-id-resolver check; it does not create a new
  module-level cycle. G2 added only `from graphql import OperationType` (third-party). **No new
  cross-folder import introduced by G2.**
- **`types/resolvers.py`** imports `from ..optimizer import logger`, `from ..optimizer._context import ...`,
  `from ..optimizer.field_meta import FieldMeta`, `from ..optimizer.plans import ...`. This is the
  **correct, documented direction** (`types/` → `optimizer/`). Decision 5 added NO new import to
  `resolvers.py` — `_fk_attname_is_deferred` reuses `getattr`/`get_deferred_fields` (stdlib/Django
  on `root`), the `_FK_ELISION_UNSAFE` sentinel is a module-local `object()`, and `force_unplanned`
  is a new kwarg on the existing `_check_n1`. So the Decision 5 `_check_n1` change introduced **no new
  coupling** — it stayed inside `resolvers.py` and the existing optimizer-context dependencies.
- **`optimizer/extension.py`** imports `..registry`, `..utils.*`, and sibling `optimizer/` modules
  including `from .walker import plan_optimizations, plan_relation`. G1 added no new import (it reused
  the already-imported `normalize_query_source`). Direction intact (extension → walker, both in
  `optimizer/`).

**Verdict: one-way dependency direction preserved.** No new cross-folder import violates the
optimizer/types boundary. The only `optimizer/ → types/` reference (walker's function-local
`origin_has_custom_id_resolver`) predates this build and is unchanged.

### Pre-step 5 — walked every accepted slice's `What looks solid` / `DRY findings` / `Notes for Worker 1` for deferred follow-ups

- **Slice 1** — no deferrals beyond "G1's GLOSSARY note → Slice 4", which Slice 4 delivered. Closed.
- **Slice 2** — `What looks solid` and `DRY findings` confirm the gate is one derived bool (clean);
  no deferred follow-up. `Notes for Worker 1`: the `force_unplanned` escalation was **resolved**
  in-cycle at Slice 2 final verification (kept as-is, no spec edit; Decision 5 prose already correct).
  One forward-looking carry-forward worth surfacing at the final gate: the **planned-but-genuinely-lazy
  pattern** — any future "strictness-visible fallback" on an elision/optimization seam must check
  whether the relation is recorded `planned` first, because `_check_n1`'s planned short-circuit
  silences strictness unless `force_unplanned` is threaded. This recurs in the `0.0.11` mutation
  cohort. (Captured for the deferred-work catalog; nothing to fix this pass.)
- **Slice 3** — the deferred G3 design is the largest carry-forward: R1 (abstract-return
  production-entry contract — the precondition), R2 (both walker inliner consumers — `_walk_selections`
  AND `_selected_scalar_names` — must use the classifier), R3 (non-Relay name-resolution + ambiguity
  contract). All preserved verbatim in spec Decision 6/7. The three `# TODO(spec-035 Slice 3)` source
  anchors stage it. Belongs to the follow-up *abstract-return optimizer entry* card, not this pass.
- **Slice 4** — `planning_state = "Needs spec"` rendering on the `DONE-035` card is an **accepted
  cross-card pre-existing condition** (matches DONE-034 "In progress" and 28+ done cards with stale
  `planning_state`); flagged for the maintainer / next-spec follow-up, not a defect, not actionable
  here.

No deferred follow-up from any slice needed to land in this integration pass.

---

## Integration-check findings

### Duplicated helpers across slices

**None.** The build introduced three new private helpers, each with a single home and a distinct
responsibility, none duplicating another:

- `walker.py::_enable_only_for_operation(info)` — the ONE place the `OperationType` comparison and the
  defensive `info.operation.operation` `getattr` chain live; the resulting bool is threaded, never
  re-derived per writer (the load-bearing DRY pin Decision 4 names).
- `resolvers.py::_fk_attname_is_deferred(root, attname)` — the Decision 5 loaded-check. A deliberate
  variant of the pre-existing `_will_lazy_load_single` keyed on the FK *column attname* (the column
  elision reads) rather than the relation *field name* — the correct axis, justified reuse of the
  `__dict__`-presence + `get_deferred_fields()` signal, not a near-copy.
- `resolvers.py::_FK_ELISION_UNSAFE` sentinel + the `force_unplanned` kwarg on the existing
  `_check_n1` — a minimal, non-breaking seam; no parallel helper.

G1 (`extension.py::_optimize` guard, shipped) is a single early-return, no helper. No file overlap
between G1 (`extension.py`), G2 (`walker.py` + `resolvers.py`), G3 (none), and Slice 4 (docs/DB), so
no cross-slice helper duplication is even possible.

### Inconsistent naming or error handling between slices (the `getattr`-defensive posture)

**Consistent across G1, G2, and Decision 5.** The package's defensive `getattr(..., default)` posture
is uniform at all three new sites:

- **G1 guard** (`extension.py::_optimize`): `getattr(result, "_result_cache", None) is not None` —
  defensive read, allocation-free `is not None` signal.
- **G2 gate** (`walker.py::_enable_only_for_operation`): `getattr(getattr(info, "operation", None),
  "operation", None)` then `operation is None or operation is OperationType.QUERY` — never raises on a
  `None`/partial `info`; the three arms (no-info, partial-info, QUERY → enabled) mirror the file's
  `runtime_path_from_info` / `_relay_max_results_from_info` idioms.
- **Decision 5 loaded-check** (`resolvers.py::_fk_attname_is_deferred`): `attname in getattr(root,
  "__dict__", {})` then a `getattr(root, "get_deferred_fields", None)` guard — same defensive shape,
  consistent with the sibling `_will_lazy_load_single`.

All three read with `getattr(..., default)` and never raise on a partial/`None` input — one coherent
posture. Error handling is also consistent: neither G1 nor G2 adds a `ConfigurationError` /
`OptimizerError` surface (confirmed — no new validation), and the Decision 5 fallback routes through
the existing `_check_n1` strictness path (the `force_unplanned` bypass makes it loud, not a new error
type). No naming drift: the `enable_only` bool name is reused verbatim across every writer signature.

### Repeated ORM/queryset patterns that should be centralized

**None new.** The Django/ORM markers in the shadow overviews are all pre-existing patterns
(`append_unique(plan.only_fields, ...)`, `Prefetch(...)`, `select_related` / `prefetch_related`
appends, `_meta.pk.attname` reads). G2 gates the existing `only_fields` writers with a single
threaded bool rather than adding new ORM calls; the `child_queryset.only(*fields)` in
`_project_scalar_only_window` is the one direct `.only()` and is correctly guarded. No new repeated
queryset-building pattern was introduced that should be extracted.

### Misplaced responsibilities between `walker.py` / `resolvers.py` / `extension.py`

**Correctly placed.** Each guard lives at its architecturally correct seam:

- **G1** in `extension.py::_optimize` only (the consumer-resolver entry; the connection field's
  `apply_to` tail is correctly NOT guarded — framework-built, never consumer-evaluated).
- **G2** at plan-**build** time in `walker.py::plan_optimizations` (NOT apply-time in `plans.py` —
  confirmed `plans.py` is untouched), so the suppression bakes into the cached plan.
- **Decision 5** at resolver-time in `resolvers.py::_build_fk_id_stub` (the one stub that reads the FK
  column), with the strictness signal routed through the existing `_check_n1` in the same module.

The one cross-module touch (the `force_unplanned` kwarg) is contained: it lives in `resolvers.py`,
set only by `forward_resolver` on the unsafe-elision path, and the second `_check_n1` caller
(`connection.py:1148`) omits it and keeps byte-identical behavior. No responsibility leaked across a
module boundary.

### Missing or too-broad exports introduced by the build (`__all__` unchanged)

**`__all__` unchanged — confirmed.** `git diff HEAD -- django_strawberry_framework/__init__.py` is
**empty**. Every new symbol is module-private: `_enable_only_for_operation`, `_FK_ELISION_UNSAFE`,
`_fk_attname_is_deferred`, and the `force_unplanned` kwarg. This matches spec Non-goals ("A new public
symbol, `Meta` key, or settings key" — out of scope) and the build-plan flag ("The card adds no public
symbol, so `__all__` is also untouched"). No too-broad or missing export.

### Repeated literals / dict keys / tuple shapes across slices

**None new across files** (see Pre-step 3). The only two literals the build introduced (`"operation"`
in walker.py, `"__dict__"` in resolvers.py) are each confined to a single file and a single
established idiom; neither appears in a second file. No new dict key or tuple shape is shared across
slices in a way that should be named.

### Whether the new comments + the GLOSSARY/README wording tell one coherent story

**Coherent.** The build's narrative is consistent across code comments and docs:

- **Code comments** consistently attribute behavior to its guard and spec decision: walker.py's
  `_enable_only_for_operation` docstring + the `plan_optimizations` "derive ONCE … thread the single
  bool" comment cite Decision 4; resolvers.py's `_FK_ELISION_UNSAFE` / `_fk_attname_is_deferred`
  comments cite Decision 5 and explain the consumer-`.only()` / B8-diffing hazard; extension.py's G1
  guard cites Decision 3. The Slice 3 `# TODO(spec-035 Slice 3)` anchors all name the spec/slice and
  describe the deferred classifier without a loud failure (correct — pass-through is the right current
  behavior).
- **GLOSSARY / README / CHANGELOG** (Slice 4) tell the SAME story at the right altitude: the
  `DjangoOptimizerExtension` body carries the G1 pass-through + G2 column-suppression bullets and the
  "what the optimizer will not touch" note; `only() projection` carries the G2 operation-type gate;
  `FK-id elision` carries the Decision 5 loaded-check; `Strictness mode` carries ONLY a G3-deferral
  pointer (no shipped G3 behavior). README/docs-README compress the same G1+G2 substance; CHANGELOG
  restates it in past-tense (`### Fixed` G1, `### Changed` G2). The single biggest coherence pin — **G3
  ships nothing on every surface** — holds: the only G3 mention anywhere is the one allowed deferral
  pointer. Code comments (G3 deferred, anchors retained) and docs (G3 deferral pointer) agree.

No contradiction between what the code does, what the comments say, and what the docs claim.

---

### Integration outcome

**No cross-slice DRY issues found. No consolidation pass is needed.**

All five required pre-steps completed: every prior `bld-slice-*.md` read in order; the static
inspection helper confirmed run (and refreshed) for every Python file with review-worthy logic
(`walker.py`, `resolvers.py`, `extension.py`) and correctly skipped for the no-`.py`-logic Slice 4;
the Repeated-string-literals sections compared (no literal in 2+ files); the Imports sections compared
(one-way `types/ → optimizer/` direction preserved, no new cross-folder coupling from G2 or the
Decision 5 `_check_n1` change); and every accepted slice's solid/DRY/Worker-1 notes walked for
deferred follow-ups (none belong in this pass; the G3 R1–R3 carry-forward and the planned-but-lazy
pattern are forward-looking, captured for the final gate's deferred-work catalog).

The integration checks are clean: no duplicated helpers, consistent `getattr`-defensive posture and
error handling across G1/G2/Decision 5, no new repeated ORM/queryset pattern, correctly-placed
responsibilities (G1 in extension `_optimize`, G2 build-time in walker, Decision 5 resolver-time in
resolvers — `plans.py` untouched), `__all__` unchanged (all new symbols module-private), no new
cross-file repeated literal/key/tuple, and one coherent story across code comments + GLOSSARY/README/
CHANGELOG (G3 ships nothing everywhere). Because the only functional code this cycle was Slice 2 (in
two files G1 does not touch) and Slices 1/3/4 added no overlapping logic, there is no surface for
cross-slice duplication.

**Status set to `final-accepted`. Worker 0 may proceed directly to the final test-run gate
(`bld-final.md`); no Worker 2 consolidation pass + Worker 3 review loop is required.**

### Summary

The four-slice spec-035 build (G1 evaluated-queryset guard — shipped `d1dea2fd`; G2 operation-type
`.only()` gating + Decision 5 FK-id-elision loaded-check — the only functional code this cycle; G3
fragment narrowing — deferred, no code; Slice 4 doc + DB wrap — no `.py` logic) integrates cleanly.
The G2 gate is a single derived `enable_only` bool threaded through all four projection writers (never
four scattered `info.operation` reads); the Decision 5 loaded-check reuses the established
`__dict__`-presence idiom on the correct axis (FK column attname) and routes its loud fallback through
the existing `_check_n1` via a minimal `force_unplanned` kwarg. No file overlap between the slices, no
new public surface, no new cross-folder coupling, no cross-file repeated literal, and one coherent
narrative across code and docs. No consolidation loop needed.

### Spec changes made (Worker 1 only)

None. Integration revealed no spec inconsistency. The spec status line (line 5: "G1 shipped
(commit `d1dea2fd`); G2 + the doc wrap remain; G3 deferred") still accurately describes the build —
G1/G2 shipped, G3 deferred, the doc wrap complete via Slice 4. No edit warranted this pass.

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
