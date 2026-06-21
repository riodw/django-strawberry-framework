# Review: `django_strawberry_framework/connection.py`

Status: verified

## DRY analysis

- Defer until a fourth synthesized-resolver shape lands; then fold the three
  `_build_connection_resolver` `_resolve` closures (connection.py:1025-1033,
  1037-1046, 1050-1058) and the relation variant (connection.py:1145-1193)
  through a shared `_run_pipeline(target_type, source, info, kwargs, *, is_async)`
  body. Today the four bodies differ on exactly two axes — sync vs async (`await`
  on the resolver call AND `await _pipeline_async`) and source acquisition
  (`initial_queryset(target_type)` / `resolver(root, info)` / windowed-rows probe).
  The sidecar-extraction line (`connection_sidecar_inputs_from_kwargs(kwargs)`)
  and the `__signature__` / `__annotations__` attachment are ALREADY single-sited
  via `_synthesized_signature` (connection.py:1060-1062, 1195-1197). Collapsing
  the remaining 3-4 lines now would hide the per-construction sync/async commit
  (Decision 10) behind a flag argument — the explicit branching is the readable
  shape while only these four colored shapes exist. Trigger: a fifth resolver
  shape, or a sync/async axis that stops being a clean 1:1 mirror.

- Defer until a third count-attachment call site appears; then extract the
  `_guard_total_count_countable(...)` + `if want_count: setattr(conn,
  _TOTAL_COUNT_ATTR, <count>)` body shared by `_attach_count_sync`
  (connection.py:681-686) and `_attach_count_async` (connection.py:689-702).
  The two are an intentional sync/async mirror that cannot collapse today — the
  async variant must `await conn_awaitable` BEFORE the guard (the await-before-raise
  `-W error` discipline) and `await nodes.acount()`, so the only truly shared
  fragment is the guard call plus the `setattr`. A `maybe-await` abstraction would
  reintroduce exactly the coroutine-color hazard the comment at connection.py:691-697
  documents. Trigger: a non-resolve_connection caller needs the same attach.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The file is the connection-surface integration
  point and consistently routes shared logic to canonical helpers rather than
  re-implementing: window-bound derivation through
  `utils/connections.py::derive_connection_window_bounds` (connection.py:294-301),
  the `Manager`->`QuerySet` + is-queryset decision through
  `utils/querysets.py::normalize_query_source` (connection.py:859), the
  deterministic total order through `optimizer/plans.py::deterministic_order`
  (connection.py:832) so plan-time and resolve-time order share one source
  (cursor-parity invariant), the count-detection fragment-descent rule through
  `optimizer/selections.py::direct_child_selected` (connection.py:388-391), the
  four target guards plus Relay-Node guard through
  `list_field.py::_validate_relay_djangotype_target` (connection.py:1236-1244),
  the nested-connection strictness check through the parameterized
  `types/resolvers.py::_check_n1` (connection.py:1178-1186), and the
  `to_attr` naming through `optimizer/walker.py::_relation_connection_to_attr`
  (connection.py:1143). The `_ends_in_unique_column` re-export (connection.py:90)
  is a deliberate single-source alias to `optimizer/plans.py::ends_in_unique_column`,
  preserving the `tests/test_connection.py` / `tests/optimizer/test_plans.py:867-869`
  import pin while keeping one implementation.
- **New helpers considered.** Both candidates above were evaluated and
  explicitly deferred with trigger conditions — collapsing them now would hide
  the sync/async per-construction commit or reintroduce coroutine-color hazards.
- **Duplication risk in the current file.** The 3x `total_count` literal
  (the field name, the `__annotations__` key, the namespace key) is confined to
  `_build_total_count_connection._populate` (connection.py:649-652) and the
  field/resolver definitions it wires; it is the GraphQL/Python member name, not
  a cross-cutting magic string, and the camelCase `totalCount` selection name
  is single-sited in `_total_count_requested` (connection.py:389). The repeated
  `models.QuerySet` `isinstance` checks (connection.py:672, 759, 784) are three
  distinct guards over three distinct misuse shapes (non-countable totalCount,
  sidecar-over-iterable, pre-sliced) — intentional parallel guard siblings, each
  with its own actionable `GraphQLError`, not consolidatable without losing the
  distinct messages.

### Other positives

- **Cursor-parity invariant is structurally enforced, not merely asserted.**
  Plan-time and resolve-time windows both derive from
  `derive_connection_window_bounds` and both order through `deterministic_order`,
  so the two halves cannot silently disagree — the load-bearing correctness claim
  is single-sourced by construction (connection.py:294-301, 832).
- **Ambiguous-empty window handling is correct and well-reasoned.**
  `_resolve_from_window` (connection.py:205-224) refuses to infer `totalCount = 0`
  for `limit == 0` (`first: 0`) / `offset > 0` (overshot `after:`) windows, falling
  back to the per-parent pipeline so byte-identical results are preserved. The
  distinction between genuinely-empty and ambiguous-empty is the subtle correctness
  edge and it is handled explicitly.
- **Await-before-raise discipline.** `_attach_count_async` (connection.py:698-701)
  awaits the queued connection coroutine before the guard can raise, so a
  guard-raise never leaves a coroutine unawaited (a hard failure under `-W error`,
  consistent with the package's `tests/conftest.py` async-leak posture).
- **Lazy-subpackage contract preserved.** The `filters` / `orders` imports are
  function-local in `_synthesized_signature` (connection.py:953-954) so bare
  `import django_strawberry_framework` does not eagerly pull the filters/orders
  subpackages — pinned by `tests/filters/test_finalizer.py` /
  `tests/orders/test_inputs.py`.
- **Fail-loud non-queryset and pre-slice guards** convert leaked Django internals
  (`Cannot reorder a query once a slice has been taken`, opaque `Int!`-null
  violations) into clear, actionable `GraphQLError`s naming the cause and the fix
  (connection.py:661-678, 748-792).
- **Concrete-class generation rationale is documented at the decision site**
  (connection.py:725-738) — handing the schema a generic alias loses the
  `resolve_connection` override at Strawberry's generic specialization, the
  spec-032 Slice-4 discovered bug; the concrete subclass survives schema build.
- **Test pins are named inline** throughout (`test_first_and_last_guard_on_generated_subclass`,
  `test_fast_path_total_count_marker_bypasses_non_queryset_guard`,
  `test_fast_path_first_zero_falls_back_for_total_count_and_pageinfo`), so a future
  editor knows which behavior each branch owes.

### Summary

`connection.py` is unchanged versus both the per-cycle baseline
(`fcf827ec`) and HEAD (`git diff` empty on both), and is a mature, well-factored
module: every shared concern is routed to a canonical helper, the sync/async and
fast-path/fallback branches are deliberate sibling shapes with documented
correctness rationale, and the cursor-parity invariant is structurally
single-sourced rather than asserted. GLOSSARY prose for `DjangoConnection`,
`DjangoConnectionField`, `Meta.connection`, and connection-aware optimizer
planning all accurately reflect the current implementation — no drift. No High,
Medium, or Low findings. Two DRY opportunities exist but are correctly deferred
with explicit trigger conditions; acting on either now would harm readability or
reintroduce coroutine-color hazards. This is a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (289 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- No GLOSSARY-only fix in scope: the connection-surface symbols
  (`DjangoConnection`, `DjangoConnectionField`, `Meta.connection`,
  connection-aware optimizer planning) were grepped in `docs/GLOSSARY.md` and the
  prose accurately reflects the current implementation — no drift, no edit owed.
- Both DRY-analysis bullets are defer-with-trigger; neither is act-now, so no
  source edit is warranted. Triggers quoted verbatim in `## DRY analysis`.
- `connection.py` is byte-identical to HEAD and to the cycle baseline
  `fcf827ec` (`git diff` empty on both), so there is no diff for Worker 3 to
  re-verify beyond the unchanged-source claim.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits: the module's docstrings and inline comments
accurately describe behavior, cite their governing spec decisions, name their
test pins, and carry no stale TODO anchors (static overview: 0 TODO comments).
Nothing to polish.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source, test, or doc edits were made this cycle (AGENTS.md #21
"Do not update CHANGELOG.md unless explicitly instructed"; the active plan
`docs/review/review-0_0_11.md` is silent on any connection.py change). Nothing to
record.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit cycle (shape #5). Core zero-edit proof holds two ways:
`git diff fcf827ec4026e800ed2ef5964279bee0e85c5509 -- django_strawberry_framework/connection.py`
empty AND `git diff HEAD -- connection.py` empty; the target is absent from
`git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`.

Independent read confirms the `None.` severities are genuine, not lazy:
- The non-queryset `totalCount` guard is single-sited in
  `_guard_total_count_countable` and shared by both `_attach_count_sync` and
  `_attach_count_async`; verified via grep that the guard call appears once per
  helper and the message is one canonical `GraphQLError`.
- Await-before-raise discipline confirmed at the source: `_attach_count_async`
  awaits `conn_awaitable` BEFORE calling the guard, so a guard-raise never leaves
  a coroutine unawaited (`-W error` posture). The guard reads only
  `nodes` / `want_count`, so awaiting first is side-effect-safe.
- Ambiguous-empty window classification in `_resolve_from_window` is correct:
  the fast-path `totalCount = 0` fires only when `offset == 0 and (limit is None
  or limit > 0)`; the `limit == 0` (`first: 0`) and `offset > 0` (overshot
  `after:`) cases return `None` to fall back to the per-parent pipeline rather
  than inferring `totalCount = 0` (Decision 5).
- The `_ends_in_unique_column` re-export is a single-source alias to
  `optimizer/plans.py::ends_in_unique_column`, identity-pinned by
  `tests/optimizer/test_plans.py` (`assert _ends_in_unique_column is
  ends_in_unique_column`) and imported by `tests/test_connection.py`.

No missed defect forces a source edit. Each Worker 2 section opens with
"Filled by Worker 1 per no-source-edit cycle pattern."

### DRY findings disposition
Both DRY items are correctly recorded as defer-with-trigger, not act-now:
- The 3x `_run_pipeline`-collapse candidate: collapsing the four resolver
  closures now would hide the per-construction sync/async commit (Decision 10)
  behind a flag argument. Trigger quoted verbatim ("a fifth resolver shape, or a
  sync/async axis that stops being a clean 1:1 mirror").
- The `_attach_count_sync` / `_attach_count_async` mirror: the async variant must
  `await` before the guard and `await nodes.acount()`, so a `maybe-await`
  abstraction would reintroduce the coroutine-color hazard the source comment
  documents. Trigger quoted verbatim ("a non-resolve_connection caller needs the
  same attach"). Neither is a GLOSSARY-only fix; no source edit owed.

### GLOSSARY drift check (#4-vs-#5 gate)
Genuine shape #5, not a missed #4. The only working-tree GLOSSARY hunk is at
line 305 — the `apps.py` Trac #37064 hardening entry (concurrent maintainer /
sibling-cycle work). The connection-surface prose is untouched by the diff and
accurate vs live source: `DjangoConnection`, `DjangoConnectionField`,
`Meta.connection`, and `Connection-aware optimizer planning` all reflect the
current implementation. No GLOSSARY fix owed by this cycle.

### Sibling / concurrent-work attribution
Working-tree dirty paths over owned dirs are
`django_strawberry_framework/management/commands/inspect_django_type.py`, its
test `tests/management/test_inspect_django_type.py`, and the `docs/GLOSSARY.md`
line-305 apps.py entry — all out-of-scope concurrent maintainer work per
AGENTS.md #33, none touching `connection.py` or connection prose. The cycle's
"Files touched: None" claim holds.

### Temp test verification
None needed — zero-edit cycle, no behavior change to pin.

### Changelog disposition
"Not warranted" verified: `git diff -- CHANGELOG.md` empty, and the disposition
cites BOTH AGENTS.md #21 and the active plan's silence. Internal-only framing
matches an empty-diff cycle.

### Validation
`uv run ruff format --check django_strawberry_framework/connection.py` — already
formatted. `uv run ruff check django_strawberry_framework/connection.py` — all
checks passed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` and marks the
`connection.py` checklist box in `docs/review/review-0_0_11.md`.
