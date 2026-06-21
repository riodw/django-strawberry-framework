# Review: `django_strawberry_framework/utils/connections.py`

Status: verified

## DRY analysis

- None — this module IS the single-source consolidation point for the two cross-subsystem contracts (window-bound derivation + the connection-sidecar kwarg family) that `optimizer/walker.py` and `connection.py` would otherwise spell twice. The sidecar kwarg names are each defined once (`CONNECTION_FILTER_KWARG` / `CONNECTION_ORDER_KWARG` at `utils/connections.py #"CONNECTION_FILTER_KWARG = "filter""`), and `has_connection_sidecar_kwargs` is composed from `connection_sidecar_inputs_from_kwargs` + `has_connection_sidecar_input` rather than re-spelling the keys. Folding the two thin presence predicates into one would erase the deliberate split between "kwargs-dict reader" (walker side) and "already-extracted pair predicate" (resolver side, used at `connection.py #"has_sidecar_input=has_connection_sidecar_input("`), which is a net-negative collapse.

## High:

None.

## Medium:

None.

## Low:

### `bool` flows through `isinstance(_, int)` in the `reverse` predicate

`derive_connection_window_bounds` keys `reverse` off `isinstance(last, int) and not isinstance(first, int)` (`utils/connections.py::derive_connection_window_bounds #"reverse = isinstance(last, int)"`). Because `bool` subclasses `int`, a literal `first=True` / `last=True` would satisfy these guards. This is **not a defect**: the helper deliberately mirrors `SliceMetadata.from_arguments`, which gates on the identical `isinstance(first, int)` / `isinstance(last, int)` (strawberry `relay/utils.py:151,164`), so plan-time and resolve-time stay in lockstep regardless — the cursor-parity invariant holds even on the pathological `bool` input, and GraphQL `Int` arguments never arrive as `bool` at runtime. Forward-looking only: defer until Strawberry's `SliceMetadata` stops gating on bare `isinstance(_, int)` (e.g. switches to `type(x) is int` or a non-bool numeric check); at that point this predicate must change in the same direction to preserve parity. No action now.

### `info` / `max_results` typed `Any` / `int | None` rather than the engine's true contract

`derive_connection_window_bounds(info: Any, ...)` and the `before`/`after`/`first`/`last` params are all `Any` (`utils/connections.py::derive_connection_window_bounds`). The `Any` on `info` is justified by the docstring — the plan-time caller passes a graphql-core `info` whose `.schema` has no `.config` (the engine reads `info.schema.config.relay_max_results` at strawberry `relay/utils.py:134`), so it is deliberately NOT a `strawberry.Info`, and `max_results` is passed explicitly to dodge that exact gap. The `Any` on the pagination args is also intentional (plan-time inline-literal coercion is the walker's concern, kept out of this module per the module docstring). Tightening `before`/`after` to `str | None` and `first`/`last` to `int | None` would more precisely document the post-coercion contract this helper assumes, but it is a pure annotation-precision nicety with zero runtime effect and a real risk of fighting the deliberate plan-time/resolve-time `Any` boundary. Defer until a typed `PaginationArgs` protocol/dataclass is introduced across the walker↔resolver boundary; fold the annotations in then.

## What looks solid

### DRY recap

- **Existing patterns reused.** `has_connection_sidecar_kwargs` composes the other two sidecar predicates instead of re-reading the kwarg keys (`utils/connections.py::has_connection_sidecar_kwargs`); `connection_sidecar_inputs_from_kwargs` is the *single* reader of `CONNECTION_FILTER_KWARG` / `CONNECTION_ORDER_KWARG` and both `connection.py` (five call sites, e.g. `connection.py #"filter_input, order_by_input = connection_sidecar_inputs_from_kwargs(kwargs)"`) and `walker.py #"if has_connection_sidecar_kwargs(arguments):"` consume them rather than spelling `kwargs.get("filter")` locally.
- **New helpers considered.** Merging `has_connection_sidecar_input` (pair predicate) and `has_connection_sidecar_kwargs` (dict predicate) into one — rejected: the two callers consume different shapes (resolver already has the extracted pair; walker has the raw arguments dict), and the current split keeps each call site at one well-named call. `ConnectionWindowBounds` was kept as a frozen dataclass returning a named triple rather than a bare tuple — correct, the `(offset, limit, reverse)` shape is read by name at both consumers (`connection.py #"offset=bounds.offset,"`, `walker.py #"return bounds.offset, bounds.limit, bounds.reverse"`).
- **Duplication risk in the current file.** The `(offset, limit, reverse)` triple appears in the dataclass fields, the docstrings, and the return — these are the type definition and its prose, not duplicated logic. The `last`-vs-`expected` limit choice is expressed exactly once at the `limit = last if reverse else slice_meta.expected` line.

### Other positives

- **Window-bound math is correct across every pagination shape.** Traced all branches against the live `SliceMetadata.from_arguments`: last-only (`end=sys.maxsize` → `expected is None`, bound = literal `last`), forward `first`-only (`limit=expected`), `before`+`last` (forward offset window, `reverse=False`, `limit=expected`), `after`+`last` (raises `UnwindowableConnection`), `after`+`first` (windowed forward offset). The `reverse` predicate and the `limit` selection are each correct and each pinned by a dedicated test (`tests/utils/test_connections.py::test_last_only_window_limit_is_literal_last_not_expected`, `::test_before_with_last_is_a_forward_window_not_reverse`, `::test_after_with_last_is_unwindowable_not_reverse_with_offset`, `::test_after_with_first_stays_a_windowed_forward_offset`, `::test_forward_window_limit_is_expected_and_not_reverse`).
- **`UnwindowableConnection` is a deliberately-distinct control-flow sentinel.** Not a `DjangoStrawberryFrameworkError`, `ValueError`, or `TypeError` — the docstring explains why (the walker catches pagination *errors* to record a field as accounted-for but must treat this shape as a fully-unplanned Decision-6 per-parent fallback). `walker.py:1352 #"except UnwindowableConnection:"` catches it separately from the `ValueError`/`TypeError` path, confirming the distinct type earns its keep. `# noqa: N818` is correctly scoped with an inline justification.
- **Cycle-safety is real and documented.** The module imports neither `connection.py` nor `optimizer/walker.py` (only `dataclasses`, `typing`, and `strawberry.relay.utils`), so both consumers import it without a cycle — the stated reason the module exists. Import-direction confirmed one-way: both consumers import from here (`connection.py:71-75`, `optimizer/walker.py:17-19`), this file imports nothing first-party. The symbols are dotted-path imports, NOT re-exported from `utils/__init__.py::__all__`.
- **`max_results` is threaded explicitly.** Passing `max_results` into `SliceMetadata.from_arguments` rather than letting the engine read `info.schema.config.relay_max_results` is the correct fix for the plan-time graphql-core `info` having no `.config`, and it guarantees plan-time and resolve-time use the same cap — the cursor-parity invariant's foundation. Both call sites pass identical keyword shape (`walker.py:1284`, `connection.py:295`).
- **Sidecar predicates fully tested.** `test_sidecar_kwarg_family_constants`, `test_connection_sidecar_inputs_from_kwargs_extracts_both`, `test_has_connection_sidecar_input_presence_predicate`, and `test_has_connection_sidecar_kwargs_combines_extraction_and_predicate` cover the constant values, extraction, the presence predicate, and the composition.

### Summary

A small (167-line), well-factored module that is itself the DRY consolidation point for two correctness contracts the optimizer planner and the Relay resolver must spell identically. The window-bound math was verified branch-by-branch against the live `SliceMetadata.from_arguments` (strawberry `relay/utils.py` lines 134/151/164/176/181) and is correct for every first/last/before/after combination, with no off-by-one in the `start`/`limit`/`reverse` derivation; the `last`-vs-`expected` limit rule and the `UnwindowableConnection` fallback are each correct and individually pinned by tests. Byte-identical to baseline `d2166ba5` (empty `git log baseline..HEAD`, empty `git diff HEAD`). No High or Medium findings; two forward-looking Lows (the `bool`-through-`isinstance` parity coupling and the deliberate `Any` typing boundary), both correct as-is and gated on explicit future triggers. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!` (pre-existing COM812-vs-formatter advisory warning only, unrelated to this file).

### Notes for Worker 3
- Shape #5 (zero tracked edits). `git diff d2166ba55cc06c28c88927e5efb49b93d45ec99f -- django_strawberry_framework/utils/connections.py` empty, `git diff HEAD -- …` empty, `git log baseline..HEAD -- …` returns nothing.
- Shadow overview used: `docs/shadow/django_strawberry_framework__utils__connections.overview.md` (+ `.stripped.py`). Not regenerated.
- Both Lows are forward-looking and explicitly trigger-gated; neither is actionable now:
  - `bool`-through-`isinstance(_, int)` parity Low — correct as-is because it mirrors `SliceMetadata`'s own `isinstance` gating (`strawberry/relay/utils.py:151,164`); trigger = Strawberry's `SliceMetadata` changing its int-gating.
  - `Any` typing-precision Low — correct as-is because the plan-time `info` is deliberately not a `strawberry.Info` (engine reads `info.schema.config.relay_max_results` at `utils.py:134`) and arg coercion is the walker's concern; trigger = a typed `PaginationArgs` boundary type landing.
- No GLOSSARY-only fix in scope: this module's symbols are dotted-path imports, not re-exported from `utils/__init__.py::__all__`. The contract-level connection prose in `docs/GLOSSARY.md` (DjangoConnectionField §324, Meta.relation_shapes §884, Connection-aware optimizer planning §262, strictness §1317) abstracts over these internal helpers — the "left unplanned … when it carries `filter:` / `orderBy:` sidecar input" / per-parent-fallback language matches the sidecar gate and `UnwindowableConnection` fallback; no drift.
- Window-bound math independently verified against the live `SliceMetadata.from_arguments`; no correctness or off-by-one finding.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits. The module/class/function docstrings are accurate (each spec-033/spec-032 decision reference matches the implemented branch), the inline comments at the sidecar-kwarg constants and the `UnwindowableConnection` raise are non-obvious-behavior explanations that earn their keep, and the `# noqa: N818` carries its own inline justification. No stale TODOs (static overview confirms zero TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source, test, or doc edits in this cycle (`AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` is silent on changelog edits for this item). Nothing to record.

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 (no-source-edit) — terminal verify.

- **Zero-edit proof, all axes clean.** `git diff d2166ba5 -- utils/connections.py` empty; `git diff HEAD -- …` empty; `git log d2166ba5..HEAD -- …` empty; owned-paths `--stat d2166ba5 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty (no sibling attribution needed this cycle); `git diff -- CHANGELOG.md` empty. "Files touched: None" holds.
- **All three Worker 2 sections** open with `Filled by Worker 1 per no-source-edit cycle pattern.`
- **High/Medium genuinely `None.`** Window-bound derivation spot-checked against the LIVE engine (`.venv/.../strawberry/relay/utils.py::SliceMetadata.from_arguments`, python 3.14): the `last`-only branch sets `end = sys.maxsize` → `expected = None`, so the `limit = last if reverse else slice_meta.expected` rule is necessary (passing `expected` would never bound the reversed window). The `reverse` predicate `isinstance(last, int) and not isinstance(first, int) and before is None` (connections.py:160) matches the documented backward-only window; `before`+`last` falls to the forward branch; `after`+`last` (reverse and `after is not None`) raises `UnwindowableConnection` (connections.py:161-164).
- **Plan-time==resolve-time window+order parity confirmed at both call sites with identical kw shape.** `connection.py:295-302` and `walker.py:1284-1291` both call `derive_connection_window_bounds(info, before=, after=, first=, last=, max_results=)` — same six keywords, same order. The walker coerces inline-literal pagination via `_coerce_pagination_int` first (walker.py:1281-1282) and passes `max_results=_relay_max_results_from_info(info)`; the resolver threads its own `max_results` (connection.py:268). Engine reads `info.schema.config.relay_max_results` (utils.py:22) — confirms the plan-time graphql-core `info` has no `.config`, the documented reason `max_results` is threaded explicitly and the `info`/arg `Any` typing is deliberate (Low #2 premise verified live).
- **`UnwindowableConnection` caught SEPARATELY from `(ValueError, TypeError)`.** walker.py:1292 `except (ValueError, TypeError): return None` (selection left unplanned but accounted-for); walker.py:1352 `except UnwindowableConnection:` is a distinct arm (fully-unplanned Decision-6 per-parent fallback). The distinct, non-`DjangoStrawberryFrameworkError`/non-`ValueError`/`TypeError` sentinel earns its keep.
- **Both Lows genuinely forward-looking / trigger-gated.** Low #1 (`bool` flows through `isinstance(_, int)`): verified `issubclass(bool, int)` is True AND the engine itself gates on bare `isinstance(first, int)` / `isinstance(last, int)` (utils.py:39,52) — so the helper mirrors the engine and parity holds even on `bool` input; trigger = Strawberry tightening its own int-gating. Low #2 (`Any` typing): premise (engine reads `info.schema.config.relay_max_results`) verified live; trigger = a typed `PaginationArgs` boundary type landing. Neither is actionable now; both correct as-is.
- **GLOSSARY / #4-vs-#5 gate.** No GLOSSARY edit (changelog/owned-paths stat empty). The module's symbols are dotted-path imports (`from .connections import …` at walker.py:17-19, connection.py:73-75), NOT re-exported from `utils/__init__.py::__all__` — private internal helpers correctly carry no GLOSSARY entry; absence is not drift. Genuine #5.
- **Cited tests grep-confirmed present** in `tests/utils/test_connections.py` (all nine: the five window-shape tests at lines 31/54/67/86/122 and the four sidecar tests at 141/148/154/161).

### DRY findings disposition
DRY-None accepted. `connection_sidecar_inputs_from_kwargs` is the single reader of the kwarg keys; `connection.py` consumes it at five sites (1027/1040/1052/1149 + the `has_connection_sidecar_input` pair predicate at 864/1150), `walker.py` consumes `has_connection_sidecar_kwargs` at 1326 — no straggler `kwargs.get("filter")`/`kwargs.get("order_by")` at any call site. Folding the pair-predicate and dict-predicate into one is correctly rejected (callers consume different shapes).

### Temp test verification
None — no temp tests created; existing suite + live-engine inspection sufficed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/connections.py` checklist box.
