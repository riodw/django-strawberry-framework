# Review: `django_strawberry_framework/connection.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: collapse the two `super(...).resolve_connection(...) -> _attach_count_*` tails.** `_consume_fallback` (`connection.py:344-347`) and the non-window tail of the generated `_build_total_count_connection.resolve_connection` (`connection.py:627-639`) are the same three-step shape: call `super().resolve_connection(nodes, info, **slice_kwargs)`, then dispatch `_attach_count_async` / `_attach_count_sync` on `inspect.isawaitable`. They differ only in the `super()` anchor class (`super(DjangoConnection, cls)` vs `super(generated, cls)`) — which MUST differ, because the fallback must skip the generated subclass's own override while the non-window tail must not. The near-copy is therefore three lines and the divergent line is load-bearing, so a shared helper would need the anchor class threaded through and would not shrink the call sites meaningfully today. Defer until a third `super().resolve_connection -> attach-count` site lands (e.g. an async connection pipeline under the 033 work); fold all three through a `_slice_then_attach_count(super_anchor, cls, nodes, want_count, **slice_kwargs)` helper at that point.
- **Act-now is NOT warranted for the sidecar/queryset guards.** `_guard_total_count_countable` (`connection.py:653-670`) and `_guard_sidecar_input_against_non_queryset` (`connection.py:740-757`) share the `... and not isinstance(x, models.QuerySet): raise GraphQLError(...)` skeleton, but the two error messages are distinct consumer-facing contracts (count-needs-queryset vs filter/order-needs-queryset) and the guards fire at different pipeline stages. Collapsing them would couple two unrelated messages behind one predicate; keep separate. (Recorded here as a considered-and-rejected candidate; the audit-trail bullet lives under `### DRY recap`.)

## High:

None.

## Medium:

### GLOSSARY drift on `DjangoConnection` — documents a return-type alias that does not exist

`docs/GLOSSARY.md:289` describes `DjangoConnection` as a "Generic return-type alias `DjangoConnection[T]` for fields that produce Relay connections. Used as the return annotation for `DjangoConnectionField` declarations." Both halves are stale against the shipped `0.0.9` implementation and this is a documented public-contract symbol (listed in the public-API index, `docs/GLOSSARY.md:27/63`), so the drift is Medium per the GLOSSARY-drift quick-check.

- It is not an "alias": `DjangoConnection` is a concrete `relay.ListConnection[NodeType]` subclass (`connection.py:450`) whose only added behavior is the `first` + `last` guard in its `resolve_connection` override; it is the base every generated `<TypeName>Connection` subclasses (`connection.py:553-558`).
- It is not "used as the return annotation for `DjangoConnectionField` declarations": `DjangoConnectionField` is a factory (`connection.py:1163`), not an annotated declaration, and the synthesized resolver's return annotation is `Iterable[target_type]` (`connection.py:952-953`), never `DjangoConnection[T]`. The module docstring (`connection.py:11-21`) and `_connection_type_for` (`connection.py:697-732`) are the source of truth: the schema always receives a generated concrete subclass, never a bare `DjangoConnection[T]` alias (the spec-032 Slice-4 bug is precisely that the bare generic alias loses the `resolve_connection` override).

Verbatim replacement text for `docs/GLOSSARY.md:289` (Worker 2 lifts directly):

> Generic Relay connection base `DjangoConnection[T]`, a `strawberry.relay.ListConnection` subclass that owns the package's `first` + `last` mutual-exclusivity guard (which Strawberry's `SliceMetadata.from_arguments` does not provide) and adds nothing else — it carries no `total_count` field. [`DjangoConnectionField`](#djangoconnectionfield) never hands the schema this generic base directly; it resolves each node type through a generated concrete `<TypeName>Connection` subclass (the `totalCount` opt-in via [`Meta.connection`](#metaconnection) only controls whether the `total_count` members are added), because a bare generic alias loses the `resolve_connection` override at Strawberry's generic specialization.

## Low:

### `total_count` field resolver `getattr` has no default — contract-guaranteed but undefended

`_build_total_count_connection.total_count` (`connection.py:581`) returns `getattr(self, _TOTAL_COUNT_ATTR)` with no default. By contract the attribute is always set before this resolver runs (the field resolves only when `totalCount` is selected, which forces `want_count=True`, which sets the attribute on every reachable path — window genuine-empty `connection.py:222`, window annotated `connection.py:254`, or fallback `_attach_count_sync`/`_attach_count_async` `connection.py:677/693`; the non-queryset path raises first via `_guard_total_count_countable`). The comment at `connection.py:579-580` documents this. No change recommended now — the code is correct and a `None` default would silently render `null` for an `Int!` field, which is worse than the `AttributeError` a genuine contract break would surface. Defer revisiting until a code path can set the connection up with `totalCount` selected but the count un-run (none exists today); flagged only so the implicit invariant is on record.

## What looks solid

### DRY recap

- **Existing patterns reused.** The window-bounds / sidecar contract is consumed from the shared `utils/connections.py` (`derive_connection_window_bounds` at `connection.py:294`, `connection_sidecar_inputs_from_kwargs` / `has_connection_sidecar_input` at `connection.py:988/1110/826`, `CONNECTION_FILTER_KWARG` / `CONNECTION_ORDER_KWARG` at `connection.py:931-951`) rather than re-spelled — this is the realized cursor-parity DRY win, so plan-time and resolve-time windows cannot drift. The deterministic-order predicate (`deterministic_order` / `ends_in_unique_column`) is imported from `optimizer/plans.py` (`connection.py:61-66`, used at `connection.py:797`), one source for plan-time window order and resolve-time pipeline order. The `_ends_in_unique_column` re-export (`connection.py:90`) preserves the spec-030 test import path against the hoist. Strictness consultation reuses the parameterized `types/resolvers.py::_check_n1` with `kind="connection_to_attr"` (`connection.py:1140-1148`) rather than a second checker — call shape matches the signature (`resolvers.py:123-165`), and correctly omits `accessor_name` since the `connection_to_attr` branch probes `to_attr` not the instance cache. `normalize_query_source` (`connection.py:822`) and `initial_queryset` (`connection.py:993`) are reused for the Manager->QuerySet coercion. The fast-path head is single-sited in `_resolve_connection_fast_path` (`connection.py:394-447`) and shared by both `resolve_connection` variants.
- **New helpers considered.** A shared `_slice_then_attach_count` for the two `super().resolve_connection -> _attach_count_*` tails was evaluated and deferred (see `## DRY analysis`) — the divergent `super()` anchor is load-bearing and only two sites exist. Merging the two non-queryset `GraphQLError` guards was evaluated and rejected — distinct consumer contracts and pipeline stages.
- **Duplication risk in the current file.** The 3x `total_count` literal (shadow "Repeated string literals") is the namespace key, the field attribute name, and the resolver binding inside `_populate` (`connection.py:642-644`) — all intrinsic to building one class namespace, not a DRY signal. The two `resolve_connection` signature blocks (`connection.py:461-472` and `584-595`) are intentional sibling overrides (base guard-only vs generated count variant); the generated one cannot inherit the signature because it threads a different `super()` anchor and the `want_count` lambda.

### Other positives

- **Fast-path correctness is well-reasoned and matches upstream.** `_resolve_from_window` (`connection.py:171-255`) derives forward-offset cursors as `_dst_row_number - 1` for every window including the reversed `last`-only one, and page flags as `first_rn > 1` / `last_rn < total` — the upstream `resolve_optimized_connection_by_prefetch` forward-window comparisons. Verified against `optimizer/plans.py:627-657`: the window keeps `_dst_row_number` forward in both branches (the reversed annotation `_dst_row_number_reversed` is plan-time `__lte`-filter only), so the resolve-time consumption is internally consistent, and `before:`/`after:` map to forward offset/limit windows through `SliceMetadata`, so the same comparisons hold.
- **Ambiguous-empty classification is the right call.** Returning `None` from `_resolve_from_window` for `limit == 0` / `offset > 0` empty windows (`connection.py:205-224`) and falling back to the per-parent pipeline (`connection.py:313-326`, `_consume_fallback`) preserves byte-identical `totalCount` / `pageInfo` for `first: 0` and overshot `after:` — the only cases where an empty optimized window is shape-indistinguishable from a genuinely empty parent. The genuine-empty `offset == 0 and (limit is None or limit > 0)` branch is the correct complement.
- **Async discipline.** `_attach_count_async` (`connection.py:681-694`) awaits the queued connection coroutine BEFORE the countability guard can raise, so a guard-raise never leaves an unawaited coroutine (a hard failure under `-W error`); the guard depends only on `nodes`/`want_count`, so awaiting first is side-effect-safe. Documented at `connection.py:683-689`.
- **Sync/async dispatch committed at construction.** `_build_connection_resolver` (`connection.py:957-1025`) freezes the resolver color per-construction because `ConnectionExtension.resolve` (sync path) does not await the inner resolver return — a per-call coroutine from a sync resolver would never be awaited. The three branches (default sync, async consumer-resolver, sync consumer-resolver) and the lazy-queryset-works-under-both rationale are correct and well-documented.
- **Selection gating scoped to direct children.** `_total_count_requested` (`connection.py:366-391`) delegates to `optimizer/selections.py::direct_child_selected` so the outer connection's `totalCount` predicate does not fire on a node-level `totalCount` deep inside `edges { node { ... } }` — avoiding a spurious `COUNT` and a spurious M1 guard once nested connections land. Correctly recurses through fragment wrappers only.
- **The `_check_n1` connection key parity is correct.** `declaring_type` + `relation_field_name` (NOT the generated connection name or accessor) + the resolve-time runtime path reproduce the walker's emission key `resolver_key(type_cls, relation_field_name, runtime_path)` (`connection.py:1140-1148`, `walker.py:1274`), the load-bearing parity for "planned -> silent". `to_attr` is keyed on `relation_field_name` via `_relation_connection_to_attr` (`connection.py:1105`), matching the walker.
- **`_consume_fallback` super-anchor is correct.** `super(DjangoConnection, cls).resolve_connection` (`connection.py:344`) reaches `ListConnection.resolve_connection` for the generated `<TypeName>Connection` MRO, bypassing both the already-applied `DjangoConnection` guard and the generated subclass's own count override — no double-guard, no fast-path re-entry.
- **Concrete-not-alias generation** (`connection.py:717-730`) and the `graphql_type_name`-not-`__name__` class naming (`connection.py:546-551`) both encode real spec-discovered bugs (lost override on generic specialization; SDL-name collision across two `Meta.name`-distinct types sharing a Python `__name__`) with thorough WHY comments.
- **Lazy subpackage import.** `_synthesized_signature` imports `filter_input_type` / `order_input_type` at call time (`connection.py:915-916`) to keep bare `import django_strawberry_framework` from eagerly pulling the `filters` / `orders` subpackages — preserving the lazy-subpackage contract, documented at `connection.py:907-914`.

### Summary

A substantial, dense, well-reasoned new file. The cursor-parity invariant (shared window-bounds, shared deterministic-order, shared sidecar-kwarg family), the windowed fast-path page-flag math, the ambiguous-empty fallback, the async await-before-raise discipline, and the per-construction sync/async commitment are all correct and verified against the shared contracts in `utils/connections.py`, `optimizer/plans.py`, and `types/resolvers.py`. No High or behaviour-changing Medium found in the source. The one real defect is documentation: the `docs/GLOSSARY.md` `DjangoConnection` entry is stale on a public-contract symbol (calls it a return-type alias used as a declaration annotation; it is a concrete `ListConnection` subclass and the resolver annotates `Iterable[T]`) — Medium, with verbatim replacement text supplied. DRY is one deferred tail-collapse opportunity gated on a third call site.

---

## Fix report (Worker 2)

Consolidated single-spawn (REVIEW shape #4): one real GLOSSARY prose fix (semantics-preserving doc edit, no source-logic change), the two Lows are no-action/forward-looking. Logic + comment + changelog dispositions recorded together; bare `Status: fix-implemented`.

### Files touched
- `docs/GLOSSARY.md:289` — replaced the stale `DjangoConnection` entry (described it as a "generic return-type alias … used as the return annotation for `DjangoConnectionField` declarations") with the artifact's verbatim replacement text describing the shipped reality: a concrete `strawberry.relay.ListConnection` subclass owning the `first` + `last` guard, never handed to the schema directly (resolved through a generated concrete `<TypeName>Connection`). No `connection.py` source change.

### Tests added or updated
- None. GLOSSARY prose fix only; no executable lines, no behaviour change. (Medium is a documentation-drift correction, not a logic fix.)

### Validation run
- `uv run ruff format .` — pass (no-changes; 265 files unchanged).
- `uv run ruff check --fix .` — pass (All checks passed; only the standing COM812-vs-formatter config warning, not an error).
- `git diff <baseline> --stat` — `docs/GLOSSARY.md | 2 +-` only; `connection.py` untouched; `uv.lock` clean.

### Notes for Worker 3
- **Verbatim-text accuracy re-confirmed against `connection.py` source before lifting** (per dispatch instruction): (1) class definition — `class DjangoConnection(relay.ListConnection[NodeType], Generic[NodeType])` at `connection.py:450`, a concrete subclass, not an alias; (2) first+last guard location — lives in the `DjangoConnection.resolve_connection` override (`connection.py:460-509`; docstring `connection.py:451-458` states "the only behavior this base adds is the Decision 3 first + last guard"); (3) resolver annotation — `return_annotation = Iterable[target_type]` at `connection.py:952`, never `DjangoConnection[T]`. Module docstring `connection.py:1-20` corroborates the "no `total_count` field" and "concrete `<TypeName>Connection`, not a bare generic alias" claims. The supplied verbatim text was accurate; no correction was needed.
- **Markdown link convention.** The replacement uses only in-page anchors — `[`DjangoConnectionField`](#djangoconnectionfield)` and `[`Meta.connection`](#metaconnection)`. In-page anchors stay inline per START.md/AGENTS.md (not converted to reference-style), so no `<!-- LINK DEFINITIONS -->` block change. Both anchor targets exist as real headings (`docs/GLOSSARY.md:293` and `:620`); verified via grep. No inline cross-file `](path)` links introduced.
- **Shadow file.** Not needed for a prose fix; consulted `docs/shadow/django_strawberry_framework__connection.overview.md` context indirectly via the artifact only — no shadow line numbers cited.
- **Low 1 (DRY defer-with-trigger) preserved as forward-looking** — no edit. Trigger intact: collapse the two `super().resolve_connection -> _attach_count_*` tails (`connection.py:344-347` and `627-639`) into `_slice_then_attach_count(super_anchor, …)` only when a 3rd call site lands under the 033 async-connection work. The divergent `super()` anchor is load-bearing today; two sites only.
- **Low 2 (guard-merge)** — considered-and-rejected by Worker 1; no action. Confirmed the two non-queryset `GraphQLError` guards carry distinct consumer-facing contracts and fire at different pipeline stages; merging would couple unrelated messages.

---

## Verification (Worker 3)

Terminal-verify on a bare `Status: fix-implemented` (shape #4 consolidated single-spawn: one GLOSSARY prose fix, no source change). Independently verified against `connection.py` source and the shared contracts in `optimizer/plans.py`, `optimizer/walker.py`, and `types/resolvers.py`.

### Diff scope
Baseline `0872a20f`, `git diff -- docs/GLOSSARY.md django_strawberry_framework/connection.py`: GLOSSARY.md only, exactly 1 line changed (`:289`, the `DjangoConnection` entry); `connection.py` untouched. No source-logic change, as the cycle claims. Owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) shows only this GLOSSARY line plus `conf.py`/`exceptions.py`/`list_field.py` hunks — those three attribute to closed sibling cycles (`rev-conf.md`, `rev-exceptions.md`, `rev-list_field.md`, all `Status: verified` and `[x]` at `review-0_0_9.md`), not a rejection trigger. Deleted root `feedback2.md`/`feedback3.md` are AGENTS.md #33 concurrent-maintainer work — left untouched.

### Logic verification outcome
- **Medium (GLOSSARY fix) — accepted.** New prose verified accurate line-by-line against source: `class DjangoConnection(relay.ListConnection[NodeType], Generic[NodeType])` is a concrete subclass (`connection.py:450`), not an alias; the `first` + `last` guard lives in its `resolve_connection` override (`connection.py:460-509`); it carries no `total_count` field (class docstring `:451-458` + module docstring `:1-20` corroborate); the synthesized resolver annotates `return_annotation = Iterable[target_type]` (`connection.py:952`), never `DjangoConnection[T]`; generation always yields a concrete `<TypeName>Connection` subclass (`_generate_connection_class`, `:553-558`). The "loses the `resolve_connection` override at generic specialization" rationale matches the module docstring's spec-032 Slice-4 note (`:14-18`). In-page anchors resolve: `#djangoconnectionfield` -> `## `DjangoConnectionField`` (`GLOSSARY.md:293`) and `#metaconnection` -> `## `Meta.connection`` (`GLOSSARY.md:620`); both exist, GitHub slugification drops backticks/dots. No inline cross-file `](path)` links introduced — link convention intact.
- **High 0 (Worker 1 logic conclusions) — spot-checked, hold.** (1) Windowed fast-path cursor/page-flag math: `_dst_row_number - 1` forward cursor for every window incl. reversed `last`-only, flags `first_rn > 1` / `last_rn < total` (`connection.py:226-255`); cross-checked the plan-time invariant in `plans.py::apply_window_pagination` (`:627-657`) — `_dst_row_number` stays FORWARD in both branches, reversed window uses `_dst_row_number_reversed` only for the `__lte` plan-time filter, so resolve-time consumption is consistent. (2) Ambiguous-empty fallback: `offset == 0 and (limit is None or limit > 0)` genuine-empty fast-path vs `return None` -> `_consume_fallback` for `first: 0`/overshot `after:` (`:205-224`, `311-326`). (3) Async await-before-raise: `conn = await conn_awaitable` (`:690`) precedes the guard (`:691`) — no unawaited-coroutine on guard-raise. (4) Sync/async commitment frozen at construction (`_build_connection_resolver`, `:957`). (5) `_check_n1` cache-key parity: `(declaring_type, relation_field_name, kind="connection_to_attr", to_attr)` (`:1140-1148`) reproduces walker's `resolver_key(type_cls, relation_field_name, runtime_path)` (`walker.py:1182`); `accessor_name` correctly omitted (the `connection_to_attr` branch probes `to_attr`, per `resolvers.py:138-159`). (6) Fallback super-anchor `super(DjangoConnection, cls)` (`:344`) reaches `ListConnection`, bypassing both the applied guard and the generated count override. No High/behavior-changing defect found that Worker 1 missed.

### DRY findings disposition
- Low 1 (defer-with-trigger: collapse the two `super().resolve_connection -> _attach_count_*` tails) preserved forward-looking — the divergent `super()` anchor (`super(DjangoConnection, cls)` at `:344` vs the generated tail's `super(generated, cls)`) is load-bearing and only two sites exist; trigger (3rd site under 033) intact. Verified the two tails genuinely differ on the anchor class.
- Low 2 (merge the two non-queryset `GraphQLError` guards) considered-and-rejected — distinct consumer contracts, different pipeline stages. Accepted.

### Temp test verification
- Temp test used: `docs/review/temp-tests/connection/probe_window_math.py` (now deleted). Reproduced the pure `_resolve_from_window` cursor/page-flag derivation in isolation: reversed `last:2`-of-5 -> forward cursors `[3,4]`, hasPrevious=True/hasNext=False; forward `first:2`-of-5 -> `[0,1]`, hasPrevious=False/hasNext=True; empty-window split classifies `offset0/limit10` genuine-empty (fast-path) vs `first:0`(limit0)/`offset5` ambiguous (fallback). All assertions passed — confirms the artifact's central cursor-parity claim. No real defect surfaced; nothing to promote.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `connection.py` box in `docs/review/review-0_0_9.md`. The diff is GLOSSARY-only (1 line, no source-logic change); the new `DjangoConnection` prose is accurate against source; Worker 1's riskiest logic conclusions (windowed cursor/page-flag math cross-checked against `plans.py`, ambiguous-empty split, async await-before-raise, `_check_n1` key parity) independently hold. Changelog `Not warranted` verified: `git diff -- CHANGELOG.md` empty, both citations present (AGENTS.md #21 + active-plan silence), internal-only doc-drift framing honest (no public-API behavior change). Ruff format-check + check clean on `connection.py`.

---

## Comment/docstring pass

Consolidated into this single spawn (shape #4). The Medium IS the documentation fix; no source comment/docstring required changes alongside it.

### Files touched
- None (beyond the GLOSSARY edit recorded in `## Fix report`).

### Per-finding dispositions
- Medium 1 (GLOSSARY drift on `DjangoConnection`): fixed — verbatim replacement text lifted into `docs/GLOSSARY.md:289` after re-confirming accuracy against `connection.py` source. The `connection.py` module docstring (`:1-20`) and the `DjangoConnection` class docstring (`:451-458`) already describe the correct behavior, so no source-side comment edit was warranted.
- Low 1 (DRY defer-with-trigger): no edit — forward-looking, trigger preserved.
- Low 2 (guard-merge): no edit — considered-and-rejected.

### Validation run
- `uv run ruff format .` — pass (no-changes).
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
GLOSSARY prose touches no source comments; nothing further.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- `AGENTS.md` #21: "Do not update CHANGELOG.md unless explicitly instructed." The dispatch prompt explicitly forbids editing `CHANGELOG.md` this cycle ("Do NOT edit `CHANGELOG.md` (record disposition in artifact)").
- Active plan is silent on changelog authorization for this per-file cycle, and per-file cycles are NEVER the authorising scope — any `CHANGELOG.md` drift forwards to the project pass.
- The edit is a documentation-drift correction in `docs/GLOSSARY.md`, semantics-preserving, with no consumer-visible behaviour change at any public API surface — internal-only by the "Not warranted" criteria.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass (no-changes).
- `uv run ruff check --fix .` — pass.

---

## Iteration log
