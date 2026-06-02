# Review: `django_strawberry_framework/optimizer/extension.py`

Status: verified

## DRY analysis

- **Defer-until-third-walker:** `_walk_directives` (lines 92-128) and `_walk_reachable_fragment_definitions` (lines 199-227) already share `_child_selections` (lines 131-145) and `_unvisited_fragment_definition` (lines 148-175); the only divergent step is "collect this node's directives" vs. "append this fragment-def to the reachable list". A `_walk_ast(node, fragments, visited, on_node, on_fragment_def)` higher-order helper would collapse both. Defer until a third selection-tree walker lands (the walker module is currently the next candidate via a future "schema audit selection-aware mode") so the joint shape can be designed once across three call sites rather than twice. Trigger: any third place in `optimizer/` that needs cycle-guarded recursive selection-set + fragment-spread descent.
- **Defer-until-second-caller:** `_strawberry_schema_from_schema` (lines 299-306) and `_strawberry_schema_from_info` (lines 309-316) read the same `_strawberry_schema` attribute through two access shapes (`schema._strawberry_schema` vs. `info.schema._strawberry_schema`); the two helpers correctly avoid sharing because the schema fallback differs (`return schema` vs. `return None`). Defer until a third entry point needs to reach the Strawberry schema, at which point a single `_strawberry_schema_of(obj, default=None)` would carry both contracts via the `default` arg. Trigger: a third Strawberry-schema reach site under `optimizer/` or any new consumer of the `_strawberry_schema` private attribute.
- **Defer-until-second-FIFO-cache:** the inline FIFO eviction at lines 650-658 (`pop(next(iter(...)))` with `_MAX_PLAN_CACHE_SIZE // 4` batch) is a self-contained eviction policy. A second bounded cache in `optimizer/` (e.g. a future field-meta cache or directive-var cache) would justify a `_evict_oldest_quarter(cache, max_size)` helper. Trigger: a second `dict`-backed bounded cache with the same eviction shape under `django_strawberry_framework/`.

## High:

None.

## Medium:

### GLOSSARY drift: `DjangoOptimizerExtension` shipped-behavior list omits four `0.0.4`–`0.0.7` consumer-visible additions

`docs/GLOSSARY.md::DjangoOptimizerExtension` (`docs/GLOSSARY.md:345-370`) is the published consumer contract for the entry point. Its `Shipped behavior` bullet list lags four consumer-visible additions that ship in `0.0.7` HEAD:

1. **Manager → `.all()` coercion (Resolver-shape contract).** `extension.py:579-580` coerces `Manager` returns via `.all()` before the `isinstance(QuerySet)` gate; the class docstring at `extension.py:474-478` documents this as a load-bearing contract. The Behavioral half is pinned by `tests/optimizer/test_extension.py:90-129` (`test_optimize_coerces_manager_through_all_records_cache_miss`) and the HTTP path it forwards to (`examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_coerces_manager_to_queryset_in_http_query`). Consumers writing `return Model.objects` (the Django shorthand) get optimization; the GLOSSARY currently only names "Django `QuerySet`s" so a reader assumes the Manager shorthand is silently passed through.
2. **FK-id elision (B2).** Already has its own dedicated entry at `docs/GLOSSARY.md::FK-id elision` (`docs/GLOSSARY.md:495-503`), but the cross-reference in the `DjangoOptimizerExtension` shipped-behavior list does not mention it as a shipped capability. The `**See also:**` line does link it. The drift is in the in-paragraph capability roll-up, which is the first place a consumer scans when evaluating the extension.
3. **Cache key splits on origin Strawberry type.** Per `spec-018-meta_primary-0_0_6.md` H2 (Slice 4), `_build_cache_key` includes `origin` as the 5th key component (`extension.py:791-797`) so a primary-return and a secondary-return resolver on the same Django model do not share a cached plan. Pinned by `tests/optimizer/test_extension.py:3015-3059` (`test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model`). The `Plan cache` entry mentions multi-type plan separation tangentially via `docs/GLOSSARY.md:719-720`, but the `DjangoOptimizerExtension` and `Plan cache` entries do not record origin-as-key-component. Multi-type is a `0.0.6` `Meta.primary` shipped feature; the cache-key behavior is its load-bearing optimizer-side consequence.
4. **Schema audit descends through union and interface types and dedupes multi-type warnings.** `_collect_schema_reachable_types` walks union `.types` (`extension.py:364-367`) and interface implementations via `schema.get_implementations` (`extension.py:376-384`). `check_schema` dedupes warnings by `(source_model, field_name)` (`extension.py:707-727`). All three are pinned: union descent by `tests/optimizer/test_extension.py:1869-1911` (`test_check_schema_descends_into_union_types`), interface implementations by `tests/optimizer/test_extension.py:1914-1964` (`test_check_schema_descends_into_interface_implementations`), multi-type dedupe by `tests/optimizer/test_extension.py:3106-3149` (`test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types`). `docs/GLOSSARY.md::Schema audit` (`docs/GLOSSARY.md:999-1005`) is a one-paragraph entry that doesn't capture either the union-and-interface walk or the multi-type dedupe.

The drift is Medium not Low because (a) the GLOSSARY entry is the published consumer contract for the optimizer entry point, (b) at least three of the four drift items are behavior-shape contracts a consumer would key against (Manager shorthand, primary vs. secondary plan separation, interface-typed root field audit), and (c) the per-file `DjangoOptimizerExtension` GLOSSARY entry is the one a consumer reads first when evaluating the package. Same Medium calibration as `rev-management__commands__export_schema.md`'s `Schema export management command` GLOSSARY drift — a public-contract entry that cumulatively lags multiple shipped polish/fix entries.

Preserve verbatim replacement prose for Worker 2 to lift:

```docs/GLOSSARY.md:355-367
Shipped behavior:

- root-gated optimization for root resolvers returning Django `QuerySet`s
- `Manager` shorthand coercion (`return Model.objects` is coerced via `.all()` and optimized as if the consumer had written `Model.objects.all()`)
- passthrough for non-root resolvers and non-`QuerySet` results
- `select_related` for safe single-valued relation chains
- `prefetch_related` for many-side relations
- generated `Prefetch` objects for child querysets
- nested prefetch chains for nested GraphQL selections
- [`only`](#only-projection) projection for selected scalar columns
- connector-column inclusion so Django can attach joined and prefetched rows without lazy loads
- [FK-id elision](#fk-id-elision) for forward-FK selections that touch only the target's `id`
- custom [`get_queryset`](#get_queryset-visibility-hook) downgrade from join to `Prefetch`
- async resolver support
- multi-type plan-cache separation: primary-return and secondary-return resolvers on the same Django model receive distinct cache entries via the resolver's origin Strawberry type
```

And for `Plan cache`'s `Selection-shape keys` bullet:

```docs/GLOSSARY.md:815
- **Selection-shape keys.** Cache keys include the selected operation AST, relevant `@skip` / `@include` variables, target model, root runtime path, and the resolver's origin Strawberry type.
```

And for `Schema audit`:

```docs/GLOSSARY.md:1003
`DjangoOptimizerExtension.check_schema(schema)` walks every schema-reachable `DjangoType` (descending through object fields, union members, and the concrete implementations of any interface type encountered, so a `DjangoType` reachable only via an interface-typed root field still participates) and reports relation targets without registered `DjangoType`s as warnings. Identical `(source_model, field_name)` warnings produced by multi-type overlap are deduped to one warning per pair so multi-type models do not double-report. Hidden fields and [`OptimizerHint.SKIP`](#optimizerhint) fields are ignored. Intended for use as a unit-test assertion or a CI gate.
```

## Low:

### Stale spec citation: `spec-014 Slice 1` → `spec-018 Slice 1`

`extension.py:700-706` contains a comment block whose first sentence claims:

```django_strawberry_framework/optimizer/extension.py:700-706
        # Dedupe (source_model, field_name) so multi-type models do not
        # double-warn: registry.iter_types() yields one entry per registered
        # type after spec-014 Slice 1, so a model with multiple types whose
        # field maps overlap on the same unregistered-target relation would
        # otherwise produce one identical warning per registered type. The
        # dedupe is a multi-type artifact, not generic defensiveness — every
        # reachable type is still audited (we cannot skip secondaries, since
        # a secondary may expose a relation the primary hides).
```

`spec-014` is `docs/SPECS/spec-014-testing_shift-0_0_4.md` (`testing_shift`, the pre-`0.0.5` test-tree restructure); it does not introduce the multi-type registry semantics. The actual spec is `docs/SPECS/spec-018-meta_primary-0_0_6.md` — the `Meta.primary` multi-type registry card. Slice 1 of spec-018 is "Registry multi-type storage + primary tracking" (see `spec-018-meta_primary-0_0_6.md` "Slice 1 — Registry multi-type storage + primary tracking" and the inline `iter_types()` shape note at the same spec) and the H3 dedupe contract in this comment block is the exact `check_schema` rationale recorded in spec-018's H3 fix.

Same Low calibration as the `spec-016 → spec-020` citation drift in `rev-list_field.md` and the `spec-020 → spec-025` drift in `rev-scalars.md` — citation hygiene (the dedupe reasoning the comment captures is correct against the actual spec; only the pointer rotted). The fix is the one-token rewrite `spec-014 Slice 1` → `spec-018 Slice 1`.

### `_walk_reachable_fragment_definitions` recurse-into-child duplication note is stale-leaning

`extension.py:217-227` recurses unconditionally into the child after the spread-handling branch:

```django_strawberry_framework/optimizer/extension.py:217-227
    for child in _child_selections(node):
        frag_def = _unvisited_fragment_definition(child, fragments, visited_fragments)
        if frag_def is not None:
            reachable.append(frag_def)
            _walk_reachable_fragment_definitions(
                frag_def,
                fragments,
                visited_fragments,
                reachable,
            )
        _walk_reachable_fragment_definitions(child, fragments, visited_fragments, reachable)
```

The docstring's tail correctly explains that the always-recurse-into-child step is a no-op for `FragmentSpreadNode` (because `_child_selections` returns `()`), but the explanation lands one branch downstream of where the unconditional recurse executes. A future reader scanning the loop body sees the unconditional recurse and has to read the docstring to confirm the no-op contract; an inline one-liner (`# No-op for FragmentSpreadNode children; harmless duplicate is cheaper than a branch.`) at the recurse line would shorten the audit pass. Defer until any change to `_child_selections`'s "return `()` for fragment spreads" contract; the docstring is currently load-bearing in lieu of an inline comment.

### `cache_info()` concurrent-access documentation lands twice with overlapping caveats

The class docstring (`extension.py:459-463`) and the `cache_info` method docstring (`extension.py:501-511`) each cover the "best-effort under concurrent access" caveat. The class-level summary references the method-level docstring ("see `cache_info` for the full caveat"), so the divergence is intentional — but the method-level paragraph is itself the second-most-detailed paragraph in the file and a one-line summary on the class docstring + verbatim deep dive on the method would let the next maintainer change one rather than two sites when the locking policy evolves. Defer until any change to `_plan_cache` synchronization shape (today: lockless `dict.pop(next(iter(...)))` exploiting CPython GIL atomicity).

### `_collect_schema_reachable_types` repeated `getattr(gql_type, "<x>", None)` pattern

The inner `_walk_gql_type` (`extension.py:340-384`) accesses `name`, `fields`, `types`, `type`, and `objects` via `getattr(..., None)` followed by an `is not None` guard at four separate sites (lines 343, 358, 364, 381). The pattern is correct (graphql-core 3.x has varied between attribute shapes across minor versions, hence the defensive sweep), but a tiny `_get(obj, attr)` helper or even a `for attr, recurse in (...)` table-driven shape would collapse the four mirror branches into one walk. Defer until graphql-core's type API stabilises further or a fifth attribute access lands; today the four explicit blocks read more clearly than a table-driven indirection.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_collect_directive_var_names` and `_collect_reachable_fragment_definitions` already share `_child_selections` (`extension.py:131-145`) and `_unvisited_fragment_definition` (`extension.py:148-175`) — the cycle-guard set is passed by reference across both walkers so a single fragment-spread visit shared between the directive walk and the reachable-definition walk costs O(1) once. The `DST_OPTIMIZER_*` key strings live in `optimizer/_context.py` and are imported at `extension.py:47-53` rather than retyped (the single-source-of-truth invariant `rev-optimizer___context.md` flagged as a Medium-if-violated holds: zero raw `"dst_optimizer*"` literals in this file).
- **New helpers considered.** A `_walk_ast(on_node, on_fragment_def)` higher-order helper consolidating the two walkers was evaluated and deferred-with-explicit-trigger above; a `_strawberry_schema_of(obj, default)` consolidating the two `_strawberry_schema_from_*` accessors was evaluated and deferred-with-explicit-trigger above; an `_evict_oldest_quarter(cache, max_size)` helper was evaluated and deferred-with-explicit-trigger above. None act-now because each currently has exactly two distinct call sites with intentionally divergent fallback semantics.
- **Duplication risk in the current file.** The four `getattr(gql_type, "<attr>", None)` branches inside `_walk_gql_type` (lines 343, 358, 364, 381) are the most copy-shaped block in the file; the Low above captures the deferral rationale (graphql-core API variance across versions, four-attribute count below a table-driven simplification threshold).

### Other positives

- **`_OriginAndModel` `NamedTuple` carries a documented pair-or-`None` contract** (`extension.py:396-411`): callers branch on `resolved is None` rather than dereferencing individual legs, and the contract is reinforced by the call site at `_optimize` (`extension.py:583-591`) using single-assignment destructuring after the `None` check. The `NamedTuple` carries the field-level types (`origin: type`, `model: type[models.Model]`) so static checkers preserve the round-trip into the walker.
- **`on_execute`'s `ContextVar` lifecycle is exception-safe** (`extension.py:518-526`): both tokens reset in `finally`, in reverse-set order (`ast_token` reset before `active_token`) so a panic in the body never strands either ContextVar in a partially-set state. The single test `test_on_execute_sets_and_resets_context_var` (`tests/optimizer/test_extension.py:694-703`) pins the entry/exit transition for the active flag; the AST cache reset is pinned indirectly by every `cache_info`-asserting test that calls `schema.execute_sync` twice (the per-execution memo must be fresh on the second call).
- **The `_print_operation_with_reachable_fragments` cache key construction stores the printed string rather than a hash** (`extension.py:750-753`'s docstring records the rationale): hash-collision risk eliminated at the cost of memory growth bounded by `_MAX_PLAN_CACHE_SIZE`. The same docstring records why the raw `loc.source.body` would be wrong (whole-document body collides across multi-operation documents). Both reasonings are load-bearing — a future "shrink the cache key" PR would have to reckon with the documented trade-offs first.
- **`_publish_plan_to_context` is called before the `is_empty` short-circuit** (`extension.py:609-611`) so strictness consumers receive the empty planned set on scalar-only queries rather than seeing a missing sentinel. The behavior is pinned by `tests/optimizer/test_extension.py:1287-1330` (`test_strictness_with_empty_plan_does_not_raise_or_warn` parametrized over `warn` and `raise`). Calling order matters here — if `is_empty` short-circuited before publish, a downstream consumer's `dst_optimizer_strictness` read would `AttributeError` on context.
- **The `frozenset[tuple[str, Any]]` hash contract for `relevant_vars`** (`extension.py:788-790`) trusts that GraphQL `variable_values` hold only JSON-shaped scalars by the time the optimizer sees them. graphql-core's variable coercion happens before resolvers run, so the `Any` is `int | float | str | bool | None | list | dict` (none of which is unhashable after the `frozenset` step except `list` and `dict` — but `relevant_vars` only enrolls variables referenced inside `@skip` / `@include`'s `if` argument, which is statically typed as `Boolean!`). The narrowing is a load-bearing invariant; loosening the directive set to permit non-Boolean `if` arguments would force a hashing rethink.
- **Test discipline:** the file pins every documented branch — Manager coercion (`test_optimize_coerces_manager_through_all_records_cache_miss`), non-QuerySet pass-through (`test_optimizer_passes_through_non_queryset`), empty-field-nodes early-return (`test_optimize_handles_empty_field_nodes`), empty plan via monkeypatch (`test_optimize_returns_original_queryset_for_empty_plan`), cache hit/miss/eviction (`test_cache_hit_on_repeated_query`, `test_cache_differentiates_queries`, `test_cache_eviction_removes_old_entries`), fragment-spread directive (`test_cache_key_includes_fragment_spread_directive_variable_value`), source-location-missing (`test_build_cache_key_is_stable_when_source_location_missing`), multi-type cache split (`test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model`), and schema-audit dedupe + secondary-only audit (`test_schema_audit_*`). Coverage shape matches every documented `_optimize` step and every documented cache-key component.
- **The lazy `from strawberry.types.nodes import convert_selections`** at `extension.py:600` is intentional and the rationale is captured at `extension.py:594-599` ("Strawberry marks `strawberry.types.nodes` as an internal surface and we do not want a hard import-time dependency on it from any caller that imports the extension only to instantiate it"). Same calibration as `apps.py`'s deferred-import-in-`ready()` from `rev-apps.md`: keep the deferred shape, do not "promote to module scope" as a Low.

### Summary

Logic is correct end-to-end against the documented O2 / O3 / O4 / O5 / O6 / B1 / B2 / B3 / B5 / B6 / B8 contracts; no High, no behaviour-changing Medium. The single Medium is GLOSSARY drift on the consumer-facing `DjangoOptimizerExtension` + `Plan cache` + `Schema audit` entries, all four items pinned by existing tests. The Lows are split between one stale spec citation (`spec-014 Slice 1` → `spec-018 Slice 1`) and three forward-looking deferrals tied to triggers the next maintainer can grep for. DRY shape evaluated and three opportunities deferred with explicit trigger conditions; no act-now consolidation candidate inside this file.

---

## Fix report (Worker 2)

### Files touched
- `docs/GLOSSARY.md` `DjangoOptimizerExtension` entry — lifted Worker 1's verbatim replacement `Shipped behavior:` block; added Manager-shorthand-coercion, FK-id-elision, and multi-type-plan-cache-separation bullets.
- `docs/GLOSSARY.md` `Plan cache` entry — extended the `Selection-shape keys` bullet with `, and the resolver's origin Strawberry type` per Worker 1's verbatim replacement.
- `docs/GLOSSARY.md` `Schema audit` entry — replaced single-paragraph body with Worker 1's verbatim replacement that names the union/interface descent and the `(source_model, field_name)` multi-type dedupe.
- `django_strawberry_framework/optimizer/extension.py` `check_schema` comment block — rotated stale `spec-014 Slice 1` → `spec-018 Slice 1` (Low (a)).

Source verification before edit: Manager coercion at `extension.py:579-580`; union-types descent at `extension.py:364-367`; interface implementations descent at `extension.py:376-384`; `origin` as the 5th cache-key leg at `extension.py:791-797`. All four match the artifact's citations.

### Tests added or updated
- None. Medium is GLOSSARY-only prose lift (no behavior change), already pinned by the artifact's enumerated tests (`test_optimize_coerces_manager_through_all_records_cache_miss`, `test_check_schema_descends_into_union_types`, `test_check_schema_descends_into_interface_implementations`, `test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model`, `test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types`). Low (a) is comment text only.

### Validation run
- `uv run ruff format .` — pass / 211 files left unchanged
- `uv run ruff check --fix .` — pass / all checks passed
- `uv.lock` — unchanged

### Notes for Worker 3
- Shadow file: not used this pass; pre-existing overviews under `docs/shadow/` were sufficient via the artifact citations.
- Deferred Lows preserved per the artifact's own trigger phrasing:
  - Low (b) `_walk_reachable_fragment_definitions` inline no-op comment — trigger: any change to `_child_selections`'s "return `()` for fragment spreads" contract.
  - Low (c) `cache_info()` two-site caveat dedupe — trigger: any change to `_plan_cache` synchronization shape (today: lockless `dict.pop(next(iter(...)))` exploiting CPython GIL atomicity).
  - Low (d) `_collect_schema_reachable_types` `getattr(gql_type, ..., None)` table-driven shape — trigger: graphql-core's type API stabilises further or a fifth attribute access lands.
- Consolidated single-spawn shape #4: Medium is GLOSSARY-only, Low (a) is one-token comment fix, Lows (b)/(c)/(d) defer explicitly.

---

## Comment/docstring pass

Discharged inside the consolidated single-spawn. The Medium is a docstring-shaped contract update (GLOSSARY entry text) and the Low (a) rotation is a source comment edit — both applied above. No further comment/docstring sweep over `optimizer/extension.py` indicated by the artifact.

### Files touched
- Same set as `## Fix report (Worker 2)` above; no additional comment/docstring edits in this sub-pass.

### Per-finding dispositions
- Medium 1 (GLOSSARY drift): applied — verbatim replacement prose lifted into the three GLOSSARY entries.
- Low (a) (stale `spec-014` citation): applied — rotated to `spec-018 Slice 1` at `extension.py:701` (post-edit line; was 702 in the artifact pre-edit).
- Low (b) (`_walk_reachable_fragment_definitions` inline no-op comment): deferred per artifact trigger.
- Low (c) (`cache_info()` two-site caveat dedupe): deferred per artifact trigger.
- Low (d) (`_collect_schema_reachable_types` `getattr` table-driven shape): deferred per artifact trigger.

### Validation run
- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

### Notes for Worker 3
Nothing additional beyond the Fix-report Notes.

---

## Changelog disposition

### State
Not warranted.

### Reason
Cycle's edits are documentation-only: GLOSSARY entry text lifts (three entries) plus a one-token comment-citation rotation inside `optimizer/extension.py`. No consumer-visible behavior changes; every cited behavior is already shipped and pinned. Per `AGENTS.md` rule "Do not update CHANGELOG.md unless explicitly instructed" and the active review plan's silence on changelog authorization for this cycle, no `CHANGELOG.md` edit is warranted.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

---

## Verification (Worker 3)

### Logic verification outcome
- Medium (GLOSSARY drift, three entries): accepted. `docs/GLOSSARY.md` `DjangoOptimizerExtension` Shipped-behavior block (lines 355-369) matches the artifact's verbatim replacement prose char-for-char; `Plan cache` Selection-shape-keys bullet (line 818) matches verbatim; `Schema audit` paragraph (line 1006) matches verbatim. Behavior spot-checks at the artifact's cited source line numbers all hold: Manager → `.all()` coercion at `extension.py:579-580` (`isinstance(result, models.Manager)` → `result.all()` then the `QuerySet` gate); union `.types` descent at `extension.py:364-367`; interface `get_implementations` descent at `extension.py:376-384` (`GraphQLInterfaceType` guard + `hasattr(gql_schema, "get_implementations")` + `.objects` tuple walk); `origin` as the 5th cache-key tuple leg at `extension.py:791-797`. The behavioral additions named in the GLOSSARY prose are pinned by the artifact's enumerated tests, all real callsites in source.
- Low (a) (`spec-014 Slice 1` → `spec-018 Slice 1`): accepted. Single-token rotation at `extension.py:701` confirmed by `grep -n "spec-018 Slice 1" extension.py` (one hit, line 701) and `grep -n "spec-014 Slice 1" extension.py` (zero hits). New anchor resolves on disk: `docs/SPECS/spec-018-meta_primary-0_0_6.md:69` carries "Slice 1: Registry multi-type storage + primary tracking", which is the multi-type registry contract the dedupe comment references.
- Lows (b), (c), (d): deferred per the artifact's own trigger phrasings — Low (b) trigger "any change to `_child_selections`'s 'return `()` for fragment spreads' contract", Low (c) trigger "any change to `_plan_cache` synchronization shape", Low (d) trigger "graphql-core's type API stabilises further or a fifth attribute access lands". All three trigger phrases reproduced verbatim in the Fix-report `Notes for Worker 3` block.

### DRY findings disposition
All three DRY items remain deferred with the artifact's verbatim trigger phrasings (third selection-tree walker, third Strawberry-schema reach site, second `dict`-backed bounded cache). No act-now consolidation; Worker 2 did not widen scope.

### Temp test verification
- No temp tests created. Medium is GLOSSARY-only prose lift (no behavior change); Low (a) is a one-token comment-citation rotation. Spot-verification at the artifact's cited line numbers + ruff gates sufficed.

### Verification outcome
cycle accepted; verified.
