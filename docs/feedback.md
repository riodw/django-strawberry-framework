# DRY review — spec-044 `DjangoDebugExtension` vs `django_strawberry_framework/utils`

Scope: every method in the 13 `utils/` modules (`__init__`, `connections`,
`converters`, `errors`, `imports`, `input_values`, `inputs`, `permissions`,
`querysets`, `relations`, `strings`, `typing`, `write_values`), reviewed
against the planned `extensions/debug.py` implementation
(`docs/spec-044-debug_extension-0_0_14.md`, Decisions 4 and 7–10), plus the
adjacent modules the extension's shape rhymes with (`optimizer/extension.py`,
`exceptions.py`, `middleware/debug_toolbar.py`, `conf.py`, `testing/`).

Verdict format follows the repo's DRY-pass discipline: **reuse is named per
item, and deliberate non-reuse carries its reason.** IDs: `R#` = reuse
obligation, `N#` = deliberate non-reuse (documented so a future worker does
not "fix" it), `X#` = new single-siting / structure opportunity inside
`debug.py` itself, `T#` = test-tier DRY. Cross-references to the spec's own
`## Helper-reuse obligations (DRY)` section (D1–D3, D-N1–D-N4) are noted where
an item extends or sharpens one.

## Headline findings

1. **Almost nothing in `utils/` is directly callable from `debug.py` — and
   that is the correct outcome, not a gap.** The utils package's charter is
   the query/write/input pipeline (visibility, inputs, windows, write
   decode); the debug extension is an engine-lifecycle instrument over
   `django.db.connections` and the execution result. Forcing reuse would
   invert DRY into coupling. The real DRY work for this card is (a) internal
   single-siting inside `debug.py` (X1–X8), (b) pattern conformance with the
   package's established idioms (R1–R6), and (c) writing the non-reuse
   reasons down (N1–N13) so the fail-loud/no-drift discipline survives review.
2. **Name-collision hazard: `utils/connections.py` is about Relay
   connections, not DB connections.** The debug extension's whole subject is
   `django.db.connections`. Nothing from `utils/connections.py`
   (window bounds, sidecar kwargs, probe arithmetic) applies, and no debug
   helper may be added there despite the name match (N1). `debug.py`'s
   docstrings should say "database connections" explicitly so grep-driven
   maintenance never conflates the two vocabularies.
3. **One genuine extraction candidate exists but should be deferred:** the
   bounded attribute-chain peel (`of_type` walks in `utils/typing.py`, the
   new `original_error` walk in `debug.py`) is a rule-of-three match on
   mechanics but not on failure policy (raise-on-cycle vs stop-on-cycle), so
   extraction is optional and not a Slice-1 obligation (X2).

## R — Reuse obligations (call or conform; do not re-spell)

- **R1 — `SchemaExtension.__init__` by omission.** `optimizer/extension.py:792`
  defines `__init__` only because it has instance config (strictness,
  strategy, plan cache). `DjangoDebugExtension` has none — Decision 6 passes
  the class and Strawberry instantiates it per operation with the
  `execution_context` kwarg. DRY-by-omission: define **no** `__init__` and
  inherit Strawberry's, which already binds `execution_context`. Do not copy
  the optimizer's ctor ceremony (its "unknown kwargs raise at construction"
  rationale has no payer here — there are no consumer kwargs).
- **R2 — the generator-hook teardown discipline.** The package already has
  one extension generator hook: `DjangoOptimizerExtension.on_execute`
  (`optimizer/extension.py:843-864`) — token sets pre-yield, `try/finally`
  restore in strict reverse order post-yield. `debug.py::on_operation` must
  mirror the same shape (acquire pre-yield, `finally`-guarded release), with
  `contextlib.ExitStack` carrying the per-alias unwind the optimizer spells
  manually for its ContextVars. Conformance, not code sharing — but a
  reviewer should be able to read the two hooks as the same idiom.
- **R3 — the bounded-walk failure idiom.** `utils/typing.py:54` pins the
  Power-of-Ten posture: an unbounded `while`-peel over an attribute chain is
  forbidden; the loop gets a fixed ceiling and a loud terminal behavior. The
  Decision-9 `original_error` chain walk must follow the same idiom — an
  identity set (its chosen guard) with iteration order bounded by the set, or
  an explicit depth cap. What it must NOT be is a bare
  `while error.original_error is not None:` loop — that is exactly the shape
  `_MAX_TYPE_WRAPPER_DEPTH` exists to forbid.
- **R4 — `exceptions.py` layering, by NOT adding to it.** The debug extension
  raises nothing of its own (capture is best-effort; the coordinator's
  contract violations cannot occur — acquire/release are private and
  bracketed). No new exception class, and no import of
  `DjangoStrawberryFrameworkError` for decoration. If a later revision does
  need a raise, it goes through `exceptions.py` (the bottom-of-import-graph
  single home), never a module-local exception class — the
  `UnwindowableConnection` precedent (`utils/connections.py:57`) shows the
  ONE sanctioned exception to that rule (a control-flow sentinel that must
  not be catchable as a package error), and debug has no such sentinel need.
- **R5 — subpackage `__init__` re-export shape.** The new
  `extensions/__init__.py` mirrors the established pattern — docstring +
  explicit re-export + tuple `__all__` — exactly as `utils/__init__.py:29-41`
  and `middleware/__init__.py` do. No wildcard, no lazy `__getattr__`.
- **R6 — settings non-surface, matching `conf.py`'s charter.** Opt-in is the
  `extensions=` list (Decision 6); there is deliberately no
  `DJANGO_STRAWBERRY_FRAMEWORK["DEBUG_EXTENSION"]` key. `conf.py` keys exist
  only where a knob must vary per deployment without code changes
  (`NESTED_CONNECTION_STRATEGY`, `TESTING_ENDPOINT`); a debug tool toggled by
  schema construction adds no such case. Named here so a reviewer doesn't
  file the "missing setting" as a gap.

## N — Deliberate non-reuse, per utils module (the full inventory)

- **N1 — `utils/connections.py` (all 12 symbols: `CONNECTION_*` kwargs,
  `UnwindowableConnection`, `connection_sidecar_inputs_from_kwargs`,
  `has_connection_sidecar_*`, `is_ambiguous_empty_window`, `WindowRangePlan`,
  `window_range_plan`, `assert_window_fetch_mode[_for]`, `split_window_rows`,
  `ConnectionWindowBounds`, `derive_connection_window_bounds`,
  `resolve_relay_max_results`, `derive_keyset_window_bounds`).** Zero
  applicability: every symbol serves Relay pagination windows. The debug
  extension's `connections.all()` loop is `django.db.connections` — a
  different noun that happens to share the module name. **Constraint:** the
  reference-counted bracket coordinator must NOT land in this module (the
  "connections helpers live in utils/connections" instinct would put DB
  instrumentation state inside the Relay-window contract module). It stays
  module-private in `extensions/debug.py` (see X5).
- **N2 — `utils/errors.py` (`field_error`, `_str_list`,
  `relation_field_error`, `validation_error_to_field_errors`,
  `join_error_path`).** These build the write-envelope `FieldError` leaf —
  a GraphQL schema type keyed by input field. The debug exception row is
  graphene's `wrap_exception` triple (`excType` / `message` / `stack`) on the
  response-extensions map — a different wire contract with no field key, no
  path segments, no codes. Funneling it through `field_error` would couple
  the debug payload to `mutations/inputs.py` (a package the extension has no
  business importing) and produce the wrong shape. The only shared atom is
  `str()` coercion — beneath extraction.
- **N3 — `utils/imports.py` (`import_attr_if_importable`, `loaded_attr`,
  `import_attr`, `require_optional_module`).** Confirms spec D-N2 and
  sharpens it: `strawberry.extensions.SchemaExtension` and
  `django.db.connections` are both hard install-time dependencies — there is
  no absent-dependency case for `require_optional_module` (contrast
  `middleware/debug_toolbar.py::require_debug_toolbar`, whose subject IS
  optional), no deferred-cycle seam for `import_attr` (debug.py sits at the
  leaf of the import graph; nothing imports back into it), and no
  best-effort probe for the other two. Plain top-of-module imports.
- **N4 — `utils/strings.py` (`snake_case`, `pascal_case`,
  `pascal_case_or_raise`, `graphql_camel_name`, `flatten_lookup_path`).**
  Tempting but wrong: deriving `isSlow` / `isSelect` at runtime via
  `graphql_camel_name("is_slow")` would make the wire bytes a function of a
  casing helper's future behavior. Decision 8's keys are a **wire contract**
  (a graphene migrant's DevTools formatter parses them); they are spelled as
  literals inside the one row serializer (X3), never computed. The other
  four helpers serve the GraphQL↔Django name boundary the extension never
  crosses (it emits no schema names).
- **N5 — `utils/typing.py` (`is_async_callable`, `unwrap_graphql_type`,
  `unwrap_container_type`, `unwrap_return_type`).** `is_async_callable`
  inspects resolver color — Decision 7 ships exactly one sync generator hook,
  no color dispatch. The unwrap trio peels `of_type` **type** wrappers; the
  debug walk peels `original_error` **error** links with different terminal
  semantics (retain a terminal `GraphQLError`, stop on cycle rather than
  raise — a malformed consumer exception chain must degrade to best-effort
  capture, not fail the whole response). Pattern conformance only (R3);
  optional extraction tracked as X2.
- **N6 — `utils/querysets.py` (all 15 symbols: `SyncMisuseError`,
  `reject_async_in_sync_context`, `model_for`, `initial_queryset`,
  `normalize_query_source`, `sync_pipeline_recourse`,
  `apply_type_visibility_*`, `visibility_scoped_related_queryset`,
  `related_visibility_queryset[_or_default]`, `_stringified`,
  `stringified_pks_present`, `pks_all_present`, `visible_related_object[s]`,
  `post_process_queryset_result_*`).** The debug extension never touches a
  queryset, a Manager, or a visibility hook — it reads `queries_log` entries
  (dicts) off connection wrappers after the fact. Notably
  `reject_async_in_sync_context` does not apply either: the extension calls
  no consumer-overridable hook, so there is no coroutine-in-sync-seam to
  guard.
- **N7 — `utils/inputs.py` (the generated-input substrate:
  `GeneratedInputFieldSpec` … `GeneratedInputArgumentsFactory`, 20+
  symbols).** The extension declares no inputs, no arguments, no generated
  types — the entire module is out of scope. Its `_safe_import` /
  namespace-clearing machinery is registry-lifecycle plumbing the extension
  (stateless across operations per Decision 6) never needs.
- **N8 — `utils/input_values.py` (`iter_input_items`, `input_field_value`,
  `is_inactive_value`, `SetInputTraversal`, `ActiveField`,
  `iter_active_fields`).** Input traversal over filter/order dataclasses;
  the extension consumes no input values. Its only "traversal" is a flat
  list slice of log entries.
- **N9 — `utils/permissions.py` (`ChannelsRequestAdapter`,
  `request_from_info`, `extract_branch_value`, `invoke_permission_method`,
  `verbatim_path`, `active_permission_*`,
  `run_active_input_permission_checks`).** No permission surface: the
  extension is all-or-nothing via schema construction (Decision 3 grounds;
  the never-in-production posture is documentation, not a runtime gate).
  `request_from_info` specifically is NOT reused because the extension never
  needs the request — SQL comes from connections, exceptions from
  `self.execution_context.result`. If a future card adds per-request gating
  (the Risks section's follow-on), `request_from_info` is the mandated entry
  point — worth one sentence in `debug.py`'s docstring only if that card
  materializes.
- **N10 — `utils/write_values.py` (`unencodable_text_error`,
  `raw_choice_value`, `coerce_relation_pk_or_none`,
  `type_check_relation_id`, `decode_scalar_leaf`, `decode_visible_relation`,
  `decode_provided_fields`).** Write-decode primitives; the extension writes
  nothing. One near-miss worth naming: `unencodable_text_error` guards
  values headed INTO the DB; the debug payload carries strings coming OUT of
  Django's own log (`last_executed_query` output, `str(exc)` messages),
  which are already Python `str` — JSON transport encoding is the runner's
  problem and the payload is JSON-serializable by construction (spec Edge
  cases). No preflight needed.
- **N11 — `utils/relations.py` (`RelationKind`, `relation_kind`,
  `is_many_side_relation_kind`, `is_forward_many_to_many`,
  `instance_accessor`, `has_composite_pk`) and `utils/converters.py`
  (`convert_with_mro`).** Relation-shape classification and field-converter
  dispatch — no relation fields, no converters in the extension.
- **N12 — `optimizer/_context.py` stash + `_active_optimizer` ContextVar
  pattern.** Confirms spec D-N1 with the concrete grounds visible in
  `optimizer/extension.py:538-604`: that machinery exists because ONE
  optimizer instance is shared across requests and must publish
  per-execution state out-of-band. Decision 6's per-operation instance makes
  plain instance attributes (`self._stash`) the correct shape — a ContextVar
  here would be cargo-culted complexity and would actually break under
  Strawberry 0.316's per-operation instantiation (no shared instance to
  coordinate).
- **N13 — `middleware/debug_toolbar.py`.** Confirms spec D-N4. Additionally
  verified: its `_HTML_TYPES` / payload-injection helpers share zero atoms
  with the extensions-map merge, so there is not even a constant to lift.

## X — Single-siting inside `debug.py` (the DRY the new module owes itself)

- **X1 — one exception serializer, one SQL-row serializer, both module-level
  functions (not closures, not methods).** `_serialize_exception(exc)` owns
  the triple (`str(type(exc))`, `str(exc)`,
  `"".join(traceback.format_exception(type(exc), exc, exc.__traceback__))`)
  — the explicit-traceback-args requirement (Decision 8) lives in exactly
  one body. `_serialize_query_row(connection, entry)` owns all six keys
  including the `float(entry["time"])` cast, the `duration > 10` predicate,
  and the `sql.lower().strip().startswith("select")` sniff — `isSlow` /
  `isSelect` are derived INSIDE it, never at a call site. Module-level so
  the Risks-section `_debug` facade fallback (and any future card) can
  import them without instantiating the extension.
- **X2 — (optional, not Slice 1) bounded-chain-peel extraction.** With the
  `original_error` walk, the package has three attribute-chain peels
  (`unwrap_graphql_type`, `unwrap_container_type`, the new walk). Mechanics
  match; failure policy does not (raise-on-cycle vs stop-on-cycle, and the
  debug walk also filters/retains terminals). If a FOURTH peel ever appears,
  promote `utils/typing.py::peel_attr_chain(obj, attr, *, should_peel,
  max_depth, on_cycle)` and rebase all four; until then a local
  `_terminal_original_error(error)` with an identity set is the simpler
  correct shape. Recorded so the future worker finds the decision instead of
  re-litigating it.
- **X3 — one slow-threshold constant.** `_SLOW_QUERY_SECONDS = 10` at module
  top (graphene's constant, Decision 8), consumed only by
  `_serialize_query_row`. Never inline `> 10` twice (serializer + docstring
  example drift is the failure mode).
- **X4 — one `original_error`-gated exception collector.**
  `_collect_exceptions(result)` owns the `result is None` guard, the
  `errors` iteration, the `original_error is not None` filter, AND the
  chain-walk + serialize compose — `get_results` and the teardown stash path
  must not each spell the None-guard (the sync parse/validation unwind hits
  it, spec Error shapes).
- **X5 — the coordinator is one private class with exactly two seams.**
  `_BracketCoordinator` (module-private, module-level singleton holding the
  lock + `{id(connection): (count, saved_flag)}` map) exposes
  `acquire(connection) -> token` / `release(token)` and nothing else. Grounds:
  (a) verified zero existing `threading.Lock` in the package — this is
  genuinely new state, so it gets the narrowest possible surface; (b) the
  package-tier concurrency tests (Test plan 8–13) need ONE seam to exercise
  overlap/restore without HTTP; (c) `ExitStack.callback(coordinator.release,
  token)` keeps the unwind wiring declarative in `on_operation`. Do NOT
  generalize it into `utils/` — one consumer (rule-of-three, same reasoning
  the spec applies to graphene's tracking port at D-N3).
- **X6 — one log-slice helper.** `_new_entries(connection, snapshot_len)`
  owns the `list(connection.queries_log)` materialization + the
  `min(snapshot, len(entries))` clamp (the bounded-deque rule, spec Edge
  cases). Teardown calls it per alias; the rollover caveat is documented on
  this ONE function, mirroring how `CaptureQueriesContext` documents the
  same limitation in one place.
- **X7 — assemble the stash through one payload builder.**
  `_build_payload(sql_rows, exceptions) -> dict` (or inline in exactly one
  teardown site) so `{"sql": [...], "exceptions": [...]}` key spelling
  exists once; `get_results` reads the stash, never constructs shape.
- **X8 — docstring vocabulary discipline.** Every helper says "database
  connection" (never bare "connection") — the disambiguation from N1 made
  structural, so `grep -rn "connection" django_strawberry_framework/utils
  django_strawberry_framework/extensions` stays partitionable by noun.

## T — Test-tier DRY

- **T1 — request-driving tier (spec D3, confirmed against `testing/`).** The
  live tests reuse `TestClient` (which already exposes response
  `.extensions` — no hand-rolled POST/JSON-decode), the single-sited
  `reload_all_project_schemas()`, `seed_data`, and `test_multi_db.py`'s
  probe-URLconf plumbing for the sharded scenario. Nothing new to build.
- **T2 — wire keys are re-spelled as literals in tests, deliberately.** The
  package-tier serializer tests must NOT import `_SLOW_QUERY_SECONDS` or
  build expected rows through `_serialize_query_row` — a self-referential
  assertion would let a key rename pass green. Anti-DRY on purpose; the wire
  contract is pinned by independent literals (`"isSlow"`, `"excType"`, …).
  This mirrors how the envelope tests pin `"__all__"` rather than importing
  the sentinel.
- **T3 — the concurrency/lifecycle mechanics tests target `X5`'s two seams
  and `X6`'s one clamp** — not the hook internals — so a future refactor of
  `on_operation`'s body (e.g. the facade fallback) does not churn the
  overlap-safety suite.

## Suggested spec deltas

Small additions to the spec's `## Helper-reuse obligations (DRY)` worth
carrying so the build handoff sees them without reading this file:

- Add **D-N5**: nothing is shared with `utils/connections.py` — Relay-window
  vocabulary, not DB connections; the bracket coordinator stays in
  `extensions/debug.py` (this file, N1/X5).
- Add **D4**: the serializers are module-level functions importable without
  the extension class, so the Risks fallback (`_debug` facade) reuses them
  (this file, X1).
- Extend **D-N1** with the sharper ground: a ContextVar stash would break
  under per-operation instantiation, not merely be unnecessary (this file,
  N12).
