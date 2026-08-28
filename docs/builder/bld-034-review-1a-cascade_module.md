# Build: R1a — conformance audit, cascade module + public surface + package tests

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` (Slice 1; Decisions 3-10; `## User-facing API` incl. `### Error shapes`; `## Goals` 1, 2, 7; the cascade-scope `## Non-goals` bullets; every `## Edge cases and constraints` bullet describing the walk; `## Test plan` `### Slice 1`; `## Definition of done` 1-5)
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`
Build plan: `docs/builder/build-034-permissions-0_0_10.md` (`## Grading rule every R1 cohort applies`, `## Ownership partition` row R1a)
Status: final-accepted

**Cohort shape.** This is a **conformance audit at `HEAD`**, not a review of a fresh diff. R1a is read-only over source and tests and writes exactly one file, this artifact. There is therefore no Worker 1 planning pass and no Worker 2 build pass for it, and no Worker 2 diff to review; the census below plus the findings are the deliverable.

---

## Plan (Worker 1)

Not applicable. This cohort lands no source and no tests. The build plan's `## Ownership partition` declares R1a read-only with a fixed audit territory; there was no planning pass to write a `### Spec slice checklist (verbatim)` or `### Dispatched findings checklist` against. The contract this pass is measured by is the build plan's `## Grading rule every R1 cohort applies`, applied to the spec territory named above.

---

## Build report (Worker 2)

Not applicable, same reason. No source, no tests, no diff. No `ruff` run was owed and none was made.

---

## Review (Worker 3)

### Method and what was actually run

| What | Command / evidence |
|---|---|
| Focused suite, R1a territory | `uv run pytest tests/test_permissions.py tests/base/test_init.py --no-cov -q` -> `73 passed, 1 skipped in 3.19s` |
| The one skip, named | `uv run pytest tests/test_permissions.py --no-cov -q -rs` -> `SKIPPED [1] tests/test_permissions.py:823: multi-DB alias pin needs the FAKESHOP_SHARDED 'shard_b' alias (settings.py)` |
| That skip, un-skipped | `FAKESHOP_SHARDED=1 uv run pytest tests/test_permissions.py -k multi_db --no-cov -q` -> `1 passed` |
| Static helper | `uv run python scripts/review_inspect.py django_strawberry_framework/permissions.py --output-dir docs/shadow` (walked below) |
| Failability proofs | `uv run python scripts/prove_failability.py docs/builder/temp-tests/review-1a/proofs.json --output docs/builder/temp-tests/review-1a/proofs-report.md` -> exit 0 |
| DoD-1 command, as the spec writes it | `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` -> `error: missing file`, **exit 2** |
| DoD-1 command, at the archived path | `... --spec docs/SPECS/spec-034-permissions-0_0_10.md` -> `OK: 42 terms`, exit 0 |
| Public surface | `git diff -- django_strawberry_framework/__init__.py` -> empty |
| Superseding-work attribution | `git log --follow --format='%h %ad %s' --date=short -- django_strawberry_framework/permissions.py`; `git log -1 --format='%B' c68aecab` |

**Tree state.** Baseline-dirty with a concurrent session's kanban work exactly as the build plan's pre-flight records, plus this cycle's own `docs/SPECS/spec-034-permissions-0_0_10.md` (Slice 0's move) and the untracked Slice 0 artifacts. No source or test file is dirty. The two transient failability mutations were reverted inside this pass and the reverts proved by byte comparison (below).

### Headline result

**Zero SKIPPED contracts.** Every divergence between the spec and `HEAD` in this territory is a **deliberate post-ship change**, and every one attributes to a commit that landed *after* `0.0.10` and that also updated the standing docs. R3 (code repair) has **no work from this cohort**; the whole population routes to R2 (spec reconciliation).

Graded population over the R1a territory. **Every number below was derived by tallying the `Grade` column of the tables in `### Contract census` and `### Test-name census`, not asserted** — re-derive with `awk '/^\| (A|B|C|D|E|F|G)[0-9]/' <this file> | awk -F'|' '{print $(NF-1)}' | sort | uniq -c`. A row whose contract split — part of the sentence still true, part superseded — is counted as **one row carrying two grades**, so the middle column sums past the row total by exactly the number of split rows; the two right-hand columns are disjoint and do sum to the row total.

**Contract census — 88 rows.**

| Grade | Rows carrying it | Rows where it is the only grade | Route |
|---|---|---|---|
| CONFORMS | 62 | 49 | none |
| SUPERSEDED | 29 | 22 | R2 |
| STALE-DESCRIPTION | 11 | 4 | R2 |
| RENAMED | 0 | 0 | — |
| **SKIPPED** | **0** | **0** | **R3 — nothing** |

13 rows are split; one of those (F13) carries three grades, which is why the middle column sums to 102 = 88 + 13 + 1. **49 rows are CONFORMS-only and 39 carry at least one grade that routes to R2** (49 + 39 = 88).

**Test-name census — 24 rows** (the spec's 23 named Slice-1 tests plus its `tests/base/test_init.py` export-pin line).

| Grade | Rows | Route |
|---|---|---|
| CONFORMS | 17 | none |
| SUPERSEDED | 6 | R2 |
| RENAMED | 1 | R2 |
| **SKIPPED** | **0** | **R3 — nothing** |

### Attribution: the superseding work, named once

Five commits touch `permissions.py` after the `0.0.10` ship (`3131a2fe Finish build-034-permissions-0_0_10.md`, 2026-06-15). Every SUPERSEDED row below attributes to one of them:

- **`c68aecab` (2026-07-16) `feat(permissions): harden cascade visibility graph, fail-closed on every SQL boundary`** — the single largest source. Its own message enumerates the five contract flips: cycles raise instead of returning un-narrowed (`fields=[]` the one permitted re-entrant shape), MTI `<parent>_ptr` links now cascade, every registered target composes its `_default_manager` subquery including identity hooks, `GenericForeignKey` / composite forward relations preflight closed, and the `__isnull=True` disjunct composes only for a nullable edge. It also added the root and hook-return validation batteries and the `.values(target_field.attname)` re-projection.
- **`90d1cf14` (2026-07-16) `fix(permissions): reject annotation aliases shadowing the cascade target column`** — the annotation-alias shadow guard in `_validated_target_subquery`.
- **`1dd9273a` (2026-07-17)** and **`60998b17` (2026-07-20) `feat(visibility): seal get_queryset hook results into framework-owned querysets`** — the sealed visibility boundary, documented after the fact by `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` (whose own header names `60998b17` as the landed implementation). This is what moved the per-edge hook call and the root preparation into `utils/querysets.py::apply_type_visibility_sync` / `::_prepared_visibility_source` behind the cascade's `_edge_error_renderer` / `_root_error_renderer` seams.
- **`dc00f4a6` (2026-08-16) `Guard diagnostic rendering against hostile consumer metadata.`**

Corroboration that these are deliberate and not drift: `docs/README.md` #"As of the cascade-hardening work on `main`, the traversal contract fails closed on every boundary the composed SQL depends on" already states the hardened contract, naming all five flips. The standing docs were updated; the archived `spec-034` was not. **`docs/SPECS/spec-051-boundary_dry_squeeze-0_0_15.md` is NOT the superseding work** — it is still `TODO-ALPHA-051-0.0.15` (planned), and its `permissions` references are to `utils/permissions.py` / `mutations/permissions.py`, not to the cascade module.

### Contract census

Evidence is symbol-qualified per `AGENTS.md` rule 27; raw `path:NN` appears only in this per-cycle artifact, always beside a symbol identifier.

#### A. `## Slice checklist` — Slice 1

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| A1 | `permissions.py` ships `apply_cascade_permissions(cls, queryset, info, fields=None)` | `django_strawberry_framework/permissions.py::apply_cascade_permissions` (permissions.py:557) | CONFORMS |
| A2 | Edge scope is `_meta.get_fields()` entries with `related_model` present AND `getattr(field, "column", None) is not None` AND NOT `getattr(field.remote_field, "parent_link", False)` | `permissions.py::_is_cascadable_edge` #"isinstance(field, models.ForeignKey) and getattr(field, \"column\", None) is not None" (permissions.py:203). `grep -c parent_link django_strawberry_framework/permissions.py` = **1**, and that one occurrence is prose in the module docstring #"MTI parent links cascade", not a predicate. The `related_model`-presence predicate is gone too: the `isinstance(ForeignKey)` test subsumes it | SUPERSEDED (`c68aecab`) |
| A3 | Excludes M2M, reverse FK, reverse OneToOne, `GenericRelation` | `permissions.py::_is_cascadable_edge` (all four fail the `isinstance(ForeignKey)` test); `permissions.py::_is_unsupported_forward_edge` explicitly keeps them skippable via `not isinstance(field, ForeignObjectRel) and not field.many_to_many and not field.one_to_many`. Pinned by `tests/test_permissions.py::test_single_column_scope_skips_m2m_reverse_and_generic` | CONFORMS |
| A4 | Excludes `GenericForeignKey` "precisely" (silently, by construction) | GFK is now **unsupported**, not excluded: `permissions.py::_is_unsupported_forward_edge`, `permissions.py::_EdgePlan.unsupported`, and the full-walk preflight `permissions.py::apply_cascade_permissions` #"cannot walk every edge of". Pinned by `tests/test_permissions.py::test_gfk_default_walk_preflights_closed` (asserts `hook_calls == []` — the preflight fires before any hook) and `::test_gfk_explicit_selection_rejected_backing_fk_supported` | SUPERSEDED (`c68aecab`) |
| A5 | Excludes the MTI `<parent>_ptr` edge "precisely" | Parent links now cascade. `permissions.py::_is_cascadable_edge` docstring #"MTI ``<parent>_ptr`` parent links included". Pinned by `tests/test_permissions.py::test_mti_parent_link_edge_included`, `::test_mti_single_level_parent_visibility_hides_child_rows`, `::test_mti_multi_level_parent_links_cascade_transitively`, `::test_mti_multiple_parent_links_both_cascade` | SUPERSEDED (`c68aecab`) |
| A6 | Resolves each edge's target through the registry primary lookup `registry.py::TypeRegistry.get` | `permissions.py::_walk` #"target_type = registry.get(field.related_model)" (permissions.py:692) | CONFORMS |
| A7 | Skips targets whose `has_custom_get_queryset()` is `False` | `grep -c has_custom_get_queryset django_strawberry_framework/permissions.py` = **0**. No hook gate exists; `permissions.py::_walk` skips only on `target_type is None`. Pinned inversely by `tests/test_permissions.py::test_identity_hook_targets_compose_default_manager` (asserts `str(result.query).count("IN (SELECT") == 2` for two identity targets) and `::test_proxy_target_filtered_default_manager_composes` | SUPERSEDED (`c68aecab`) |
| A8a | Intersects `Q(<field>__in=<target visible pks>)` | `permissions.py::_walk` #"condition = Q(**{f\"{field.name}__in\": subquery})" | CONFORMS |
| A8b | ...`| Q(<field>__isnull=True)`, unconditionally | Conditional: `permissions.py::_walk` #"if field.null:". Pinned by `tests/test_permissions.py::test_isnull_disjunct_only_on_nullable_edges` | SUPERSEDED (`c68aecab`) |
| A9 | Target subquery pinned to `queryset.db` | `permissions.py::_walk` #"_default_manager.using(state.alias).all()", where `state.alias` is set from the root call's `queryset.db` in `permissions.py::apply_cascade_permissions` #"alias=queryset.db". Pinned by `tests/test_permissions.py::test_multi_db_subquery_pinned_to_caller_alias` (passes under `FAKESHOP_SHARDED=1`) | CONFORMS |
| A10 | Cycle detection via a module-level `ContextVar` **seen-set**, "the upstream `_cascade_seen` shape verbatim" | `permissions.py::_TraversalState` is a frozen dataclass carrying `alias` / `active` / `path`; the var is `permissions.py #"_cascade_state: ContextVar[_TraversalState | None]"`. `grep -c _cascade_seen django_strawberry_framework/permissions.py` = **0** | SUPERSEDED (`c68aecab`) |
| A11 | Re-entry on a type already in the set returns the partially-narrowed queryset **without raising** | `permissions.py::_cycle_error` + `permissions.py::apply_cascade_permissions` #"raise _cycle_error(state, cls)". The one permitted re-entrant shape is `fields=[]`: #"if names_to_walk == set():". Pinned by five rows (see the failability proof below) | SUPERSEDED (`c68aecab`) |
| A12 | The root call resets the var in a `finally`; request isolation under WSGI and ASGI | `permissions.py::apply_cascade_permissions` #"finally:" / #"_cascade_state.reset(token)"; per-edge frames likewise in `permissions.py::_walk`. Pinned by the autouse `tests/test_permissions.py::_assert_contextvar_clean` fixture, `::test_hook_exception_propagates_and_resets_state`, `::test_two_overlapping_threads_isolate_traversal_state`, `::test_aapply_gather_restores_task_contexts` | CONFORMS |
| A13 | `fields=` bare string rejected up front by an `isinstance(fields, str)` guard | `permissions.py::_validate_fields` #"if isinstance(fields, str):". Pinned by `tests/test_permissions.py::test_fields_bare_string_raises` | CONFORMS |
| A14 | Unknown and known-but-non-cascadable names raise `ConfigurationError` naming the field, the model, and the cascadable set | `permissions.py::_validate_fields` #"are not cascadable; the cascadable edges are". Pinned by `::test_fields_unknown_name_raises`, `::test_fields_non_cascadable_name_raises` | CONFORMS |
| A15 | Sync misuse: a coroutine return closes the coroutine and raises `SyncMisuseError`, "reusing the probe shape of `utils/querysets.py::apply_type_visibility_sync`" | Behaviour holds — `permissions.py::_walk` #"apply_type_visibility_sync(" -> `utils/querysets.py::reject_async_in_sync_context`, which closes the coroutine (`utils/querysets.py::_dispose_sync_awaitable`). Two description defects: the cascade **delegates the whole hook invocation**, it does not re-implement a probe shape; and the guard tests `inspect.isawaitable`, not `inspect.iscoroutine`, so any awaitable is rejected. Pinned by `::test_sync_helper_raises_syncmisuseerror_on_async_target_hook` | CONFORMS / STALE-DESCRIPTION |
| A16 | `aapply_cascade_permissions` wraps the sync walk in `sync_to_async(thread_sensitive=True)` "(the `filters/sets.py` precedent)" | `permissions.py::aapply_cascade_permissions` #"await run_in_one_sync_boundary(" -> `utils/querysets.py::run_in_one_sync_boundary` #"sync_to_async(fn, thread_sensitive=True)". The semantics are identical; the shape is now the shared one-boundary primitive (spec-040 D17), not a direct call, and `filters/sets.py` is no longer the precedent it names | CONFORMS / STALE-DESCRIPTION |
| A17 | Both symbols export from the package root and join `__all__`; the exports pin in `tests/base/test_init.py` grows | `django_strawberry_framework/__init__.py` #"from .permissions import" and `__all__` entries `"aapply_cascade_permissions"` / `"apply_cascade_permissions"`; `tests/base/test_init.py::test_public_api_surface_is_pinned` asserts the full `__all__` tuple including both, and `::test_star_import_preserves_namespace_hygiene` proves each `__all__` name imports | CONFORMS |
| A18 | New `tests/test_permissions.py` including the four dedicated upstream-invariant pins | File exists; all four invariants carry a dedicated row (cycle -> `::test_mutual_cycle_fails_closed_with_path`, scope -> `::test_single_column_scope_skips_m2m_reverse_and_generic`, alias -> `::test_multi_db_subquery_pinned_to_caller_alias`, nullable -> `::test_nullable_fk_rows_preserved`). The cycle pin's *contract* is inverted per A11 | CONFORMS (cycle row's contract SUPERSEDED) |

#### B. Decisions 3-10

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| B1 | D3: source is the flat `django_strawberry_framework/permissions.py`; no new subpackage | File exists at that path; helper reports 18 symbols, no subpackage | CONFORMS |
| B2 | D3: contents are "the two public functions, the module-level `ContextVar`, and the private walk/validation helpers" | True, plus a third module-level public name the sentence omits: `permissions.py #"from .utils.querysets import SyncMisuseError as SyncMisuseError"` (redundant-alias re-export). The module's own comment argues it adds no *new* public name because `SyncMisuseError` is already in the root `__all__` via `types`; the Decision's inventory sentence is still incomplete | STALE-DESCRIPTION |
| B3 | D3: tests at `tests/test_permissions.py`, mirroring the flat module | Exists | CONFORMS |
| B4 | D4: exact names and signatures for both helpers; both re-exported from `__init__.py` and in `__all__` | See A1 / A17 | CONFORMS |
| B5 | D5 step 1: the three-predicate edge scope | See A2 / A4 / A5 | SUPERSEDED |
| B6 | D5 step 2: `registry.get(field.related_model)`; no registered type -> edge skipped | `permissions.py::_walk` #"if target_type is None:" / #"continue". Pinned by `::test_unregistered_target_model_skipped` | CONFORMS |
| B7 | D5 step 3: hook gate — `has_custom_get_queryset()` must be `True`; the identity default is skipped "with zero SQL emitted" | See A7. Note this reverses a **rejected alternative** recorded in the rationale companion (`## Decision 5` -> "Calling every target's `get_queryset` unconditionally (upstream behavior). Rejected: identity hooks generate `__in (SELECT pk FROM target)` clauses that constrain nothing and cost real SQL"). The reversal has a stated security reason (`permissions.py` module docstring #"a registered proxy type whose filtered ``_default_manager`` IS its visibility policy"), so it is a Post-ship reversal for R2 to record, not an alternative to re-argue | SUPERSEDED (`c68aecab`) |
| B8 | D5 step 4: `target_qs = TargetType.get_queryset(related_model._default_manager.using(queryset.db).all(), info)`, then `.filter(Q(__in) | Q(__isnull))`; `_default_manager` not `.objects` | `_default_manager` and the `.using(...)` seed hold (`permissions.py::_walk`). Two additions the Decision does not state: the hook call is routed through the sealed boundary, and the return is validated and **re-projected** (`permissions.py::_validated_target_subquery` #"return target_qs.values(attname)"). Disjunct conditionality per A8b | CONFORMS (seed) / SUPERSEDED (return handling, `c68aecab` + `60998b17`) |
| B9 | D5 step 5: seen-set install / `finally` clear / re-entry returns unchanged / frame discards its own class on exit | Install + `finally` clear + frame discard hold (A12; `::test_acyclic_diamond_composes_sink_through_both_branches` proves two sibling edges to one sink both cascade). Re-entry per A11 | CONFORMS (lifecycle) / SUPERSEDED (re-entry) |
| B10 | D6: hidden-FK target -> the **parent row is excluded**; nulling and sentinels rejected | `permissions.py::_walk` composes a `.filter(...)`. Pinned by `::test_cascade_excludes_rows_with_hidden_targets` | CONFORMS |
| B11 | D6: no existence leak — hidden-target and missing-target rows equally absent | Pinned by `::test_hidden_and_missing_targets_indistinguishable` | CONFORMS |
| B12 | D6 Consumer-recipe divergence: `django_strawberry_framework/types/resolvers.py::_make_relation_resolver #"return getattr(root, field_name)"` "reads the forward FK by bare accessor with no `DoesNotExist` / sentinel fallback" | **The cited substring does not exist at `HEAD`** (`grep -c 'return getattr(root, field_name)' django_strawberry_framework/types/resolvers.py` = 0; the symbol is at resolvers.py:475). Worse, the *premise* is false: the forward-FK branch now reads `getattr(root, accessor_name)` and routes it through `types/resolvers.py::_visible_related_object` whenever `types/resolvers.py::_custom_visibility_type` returns a target type with a custom hook, so a hidden forward-FK target resolves to `None` at the field. The block's conclusion (fakeshop cascades in every non-staff branch) may still be what fakeshop does — that is R1c's territory — but its stated reason is no longer true | STALE-DESCRIPTION |
| B13 | D7: the cascade composes unevaluated `__in` subqueries and adds **zero** query round-trips | `permissions.py::_walk` never evaluates. Pinned by `::test_cascaded_traversal_adds_zero_queries` and, incidentally, by `::test_identity_hook_targets_compose_default_manager`'s `django_assert_num_queries(1)` over a two-subquery shape | CONFORMS |
| B14 | D8: every per-edge subquery is built from `_default_manager.using(queryset.db)` — the resolved alias, not `_db` | `permissions.py::apply_cascade_permissions` #"alias=queryset.db" (the public property) feeding `permissions.py::_walk` #".using(state.alias)". Tightened, not weakened: a nested application on a divergent alias now fails closed (#"nested walk for" ... #"but the root cascade is pinned to"), pinned by `::test_nested_application_off_root_alias_fails_closed`, and a hook return explicitly routed off the alias fails closed through `permissions.py::_edge_error_renderer`'s `alias` branch | CONFORMS (the added rejections are unstated in the spec — see F-series) |
| B15 | D9: `fields=` accepts an iterable of names and scopes the walk | `permissions.py::_validate_fields` + `permissions.py::_walk` #"if names_to_walk is not None and field.name not in names_to_walk:". Pinned by `::test_fields_scopes_walk` | CONFORMS |
| B16 | D9: bare string rejected first, before any name lookup | `permissions.py::_validate_fields` — the `isinstance(fields, str)` guard is the first statement after the `None` short-circuit | CONFORMS |
| B17 | D9: a name whose edge is cascadable but whose target "has no registered type **or no custom hook**" is accepted and skipped | Only the no-registered-type half survives. A hookless registered target now composes (A7). The live test is `::test_fields_valid_but_unregistered_target_accepted` | SUPERSEDED (`c68aecab`) |
| B18 | D9: the check is a per-call set comparison, redundant-but-bounded | `permissions.py::_validate_fields` #"requested - cascadable" over the `lru_cache`d `permissions.py::_edge_plan`. Still per-call; the edge classification is now memoized per model, which is the memo the held-back justification anticipated | CONFORMS |
| B19 | D10: sync helper probes each target-hook invocation and raises `SyncMisuseError` naming the target type and the two recourses "(`aapply_cascade_permissions`, or a sync hook rewrite)" | The raise and the type name hold. The **recourses named are different**: `permissions.py #"_ASYNC_RECOURSE"` says neither variant can await, and names "make this target type's `get_queryset` sync, or pass `fields=` to skip the async-hooked edge". `::test_sync_helper_raises_syncmisuseerror_on_async_target_hook` asserts exactly that and asserts the Relay wording is *absent*. Note D10's own third bullet already states the `fields=` recourse, so the spec contradicts itself here | SUPERSEDED (`c68aecab`) |
| B20 | D10: async helper is a `sync_to_async(thread_sensitive=True)`-wrapped execution of the sync walk | See A16 | CONFORMS / STALE-DESCRIPTION |
| B21 | D10: the `ContextVar` survives the async->sync boundary because asgiref copies the context; install/reset never leaks back into the event-loop task | Pinned by `::test_aapply_runs_walk_off_event_loop` (asserts `_cascade_state.get() is None` in the caller after the await) and `::test_aapply_gather_restores_task_contexts` | CONFORMS |
| B22 | D10: an `async def` target hook raises `SyncMisuseError` from **both** variants | Pinned by `::test_aapply_async_target_hook_still_raises` | CONFORMS |

#### C. `## User-facing API` and `### Error shapes`

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| C1 | Two new public symbols, no new `Meta` key, no constructor argument; the cookbook line is the whole consumer surface | `__init__.py::__all__`; `permissions.py::apply_cascade_permissions` signature | CONFORMS |
| C2 | The user is resolved through `info.context.request.user`, "the same path `utils/permissions.py::request_from_info` ... take" | `django_strawberry_framework/utils/permissions.py::request_from_info` exists (utils/permissions.py:221). Its signature has grown a keyword-only `family_label`; the spec names only the symbol | CONFORMS |
| C3 | Transitive composition `Entry -> Item -> Category` "with the `ContextVar` seen-set breaking cycles" | Transitivity holds (`::test_transitive_cascade_two_deep`); the cycle half is A11 | CONFORMS (transitivity) / SUPERSEDED (cycle half) |
| C4 | `fields=["item"]` scopes the walk | `::test_fields_scopes_walk` | CONFORMS |
| C5 | `qs = await aapply_cascade_permissions(cls, qs, info)` | `permissions.py::aapply_cascade_permissions` | CONFORMS |
| C6 | Error shape: unknown / non-cascadable `fields=` -> `ConfigurationError` naming entry, model, cascadable set | A14 | CONFORMS |
| C7 | Error shape: bare-string `fields=` -> `ConfigurationError` naming the non-string-iterable requirement | A13; `permissions.py::_validate_fields` #"must be a non-string iterable of" | CONFORMS |
| C8 | Error shape: async target hook -> `SyncMisuseError` "pointing the consumer at `aapply_cascade_permissions` or a sync hook rewrite" | B19 | SUPERSEDED |
| C9 | Error shape: "Cycles never raise: re-entry returns the partially-narrowed queryset" | A11 | SUPERSEDED |
| C10 | Error shape: hidden targets never raise and never leak existence | B11 | CONFORMS |
| C11 | `### Error shapes` is the complete list of the helper's error surface | It is not. `HEAD` raises `ConfigurationError` from **ten** further shapes the section never mentions, each with its own message: non-iterable `fields=` and non-string `fields=` entries (`_validate_fields`); a `fields=` name matching an unsupported forward relation (`_validate_fields` #"have no single-column cascade semantics"); the full-walk unsupported-edge preflight (`apply_cascade_permissions` #"cannot walk every edge of"); the cycle error (`_cycle_error`); a nested application off the root alias (`apply_cascade_permissions` #"nested walk for"); a sliced root and a combined root (`_validate_root_queryset`); the root seal defects (`_root_error_renderer`'s `type` / `table` / `untrusted`); and the hook-return battery (`_validated_target_subquery`'s sliced / combined / `distinct_fields` / grouped / alias-shadow, plus `_edge_error_renderer`'s `type` / `table` / `untrusted` / `alias`) | STALE-DESCRIPTION |

#### D. `## Goals` 1, 2, 7

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| D1 | Goal 1 invariant: `ContextVar` cycle guard — "partial-narrow on cycle break, **never a raise**" | A11 | SUPERSEDED |
| D2 | Goal 1 invariant: single-column forward scope | Holds in substance (only single-column concrete forward FK / O2O compose); the predicate spelling and the MTI / GFK memberships are A2 / A4 / A5 | CONFORMS |
| D3 | Goal 1 invariant: nullable-FK preservation | `::test_nullable_fk_rows_preserved`, `::test_nullable_chain_preserves_null_links_and_drops_hidden_tails`. The disjunct is now conditional (A8b), which narrows the emitted SQL without changing the invariant: a nullable edge still gets it | CONFORMS |
| D4 | Goal 1 invariant: caller-alias pinning | B14 | CONFORMS |
| D5 | Goal 2: sync rejects async target hooks; `aapply` wraps the walk so async resolvers compose without blocking the loop | A15 / A16 / B22 | CONFORMS |
| D6 | Goal 7: composable rules visible from the owning type; no global registry of permission rules, no schema-level configuration | The helper is called from inside a consumer `get_queryset`; `grep -ci cascade django_strawberry_framework/conf.py` = 0 | CONFORMS |

#### E. `## Non-goals` (cascade scope)

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| E1 | M2M and reverse-relation cascade visibility deferred whole | A3; `permissions.py::_is_unsupported_forward_edge` keeps them explicitly skippable | CONFORMS |
| E2 | No `bypass_get_queryset` escape hatch; a consumer scopes with `fields=` | No such symbol in `permissions.py`; `fields=` is the scoping tool | CONFORMS |
| E3 | Async-native cascade walking deferred; async target hooks raise `SyncMisuseError` from both variants in `0.0.10` | B22 | CONFORMS |
| E4 | No new `DJANGO_STRAWBERRY_FRAMEWORK` settings key | `grep -ci cascade django_strawberry_framework/conf.py` = 0 | CONFORMS |

#### F. `## Edge cases and constraints` — every bullet describing the walk

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| F1 | Nullable FK rows preserved by the `__isnull=True` disjunct | D3 | CONFORMS |
| F2 | Empty visible set: every non-null-FK row drops, null-FK rows survive, no error, no leak | `::test_nullable_fk_rows_preserved` (the hook returns `qs.none()`) | CONFORMS |
| F3 | Self-referential FK: "the type cascades into itself; the seen-set breaks the recursion at depth 1 ... the target hook's nested cascade call returns un-narrowed rather than recursing forever" | Fails closed. `::test_self_referential_cascading_hook_fails_closed`; the documented recourse is pinned by `::test_self_referential_fields_scoping_breaks_recursion` | SUPERSEDED (`c68aecab`) |
| F4 | Mutual cascade A<->B: "the seen-set breaks the loop with the partially-narrowed queryset; both directions still apply each other's *direct* narrowing" | `::test_mutual_cycle_fails_closed_with_path`, `::test_longer_cycle_renders_full_path`, `::test_cyclic_diamond_fails_closed` | SUPERSEDED (`c68aecab`) |
| F5 | Frame-exit discard: two sibling FK edges to the same target both cascade; the set guards ancestry, not visit count | `::test_acyclic_diamond_composes_sink_through_both_branches` | CONFORMS |
| F6 | `ContextVar` isolation across requests and across the `sync_to_async` boundary | A12 / B21 | CONFORMS |
| F7 | Unregistered target model -> edge skipped; a model exposed only through a secondary type cascades through that type | B6; `registry.py::TypeRegistry.get` returns the single registered candidate when no primary is declared, which is exactly what `tests/test_permissions.py::_make_type(..., primary=False)` relies on throughout | CONFORMS |
| F8 | Secondary types are never cascade targets | `::test_secondary_type_never_cascade_target` | CONFORMS |
| F9 | A secondary type **as the root** narrows transitive re-reaches through the primary, "and the walk still terminates (the primary lands in the set on its own first visit)" | Resolution-through-the-primary holds; termination is now by fail-closed raise, not by silent un-narrowing. `::test_secondary_root_self_edge_reaches_primary_then_fails_closed` asserts the path `SelfRefSecondaryType.parent -> SelfRefPrimaryType.parent -> SelfRefPrimaryType` | SUPERSEDED (`c68aecab`) |
| F10 | `Meta.fields`-excluded FK edges still cascade | `permissions.py::_edge_plan` reads `model._meta.get_fields()`, never the type's selected fields; the whole test file's `_make_type(..., fields=("id",))` default exercises this on every row | CONFORMS |
| F11 | Non-nullable forward-FK target hidden -> the parent row drops, not a nested `null`; the to-many shape is pinned by `test_nested_relation_traversal_respects_target_cascade` | `permissions.py::_walk` composes a `.filter(...)`; `tests/test_permissions.py::test_nested_relation_traversal_respects_target_cascade` exists | CONFORMS |
| F12 | Composite-PK / composite-FK targets "skipped by the scope test exactly as M2M is" | Not skipped — a composite / multi-column `ForeignObject` is an *unsupported* forward relation and preflights closed, exactly as the GFK does (`permissions.py::_is_unsupported_forward_edge` docstring #"composite / multi-column ``ForeignObject``"; `permissions.py::_EdgePlan.unsupported`) | SUPERSEDED (`c68aecab`) |
| F13 | `GenericForeignKey` / `GenericRelation` excluded by the same two-predicate scope test | `GenericRelation` half CONFORMS (still skipped, now because it is not a `ForeignKey` / is `one_to_many`); the GFK half is A4; the "two-predicate scope test" description is A2 | SUPERSEDED (GFK) / CONFORMS (`GenericRelation`) / STALE-DESCRIPTION (predicate) |
| F14 | MTI parent link excluded by design, with a *deferred extension* if a consumer later wants it | A5. The deferred extension shipped as the default | SUPERSEDED (`c68aecab`) |
| F15 | Cascade-target hook return contract: the helper "does not defensively rewrite the hook's return (a hook returning a non-row queryset is a consumer bug, surfaced by the backend or by wrong results, not silently absorbed)" | Inverted. Returns are now validated and normalized: `permissions.py::_validated_target_subquery` rejects sliced / combined / field-`distinct` / grouped / alias-shadowing returns and re-projects the rest to `.values(field.target_field.attname)`; the shape / concrete-table / alias half moved into `utils/querysets.py::_normalized_visibility_result` behind `permissions.py::_edge_error_renderer`. Pinned by `::test_hook_return_rejections_fail_closed`, `::test_hook_values_and_values_list_projections_are_normalized`, `::test_to_field_edge_compares_target_column`, `::test_annotation_alias_shadow_cannot_bypass_visibility`, `::test_annotation_alias_shadow_to_field_cannot_bypass_visibility`, `::test_hook_manager_return_is_coerced`, `::test_unpinned_hook_return_is_repinned_to_root_alias`. The spec's own worked examples are now wrong in both directions: a `.values("col")` return no longer "silently compares the FK against the wrong column" (it is re-projected), and a multi-column `.values()` no longer raises `ValueError` | SUPERSEDED (`c68aecab`, `90d1cf14`, `60998b17`) |
| F16 | Abstract-base hooks: `has_custom_get_queryset()` reports overrides through abstract bases, "so a cascade target whose hook lives on a shared base participates" | The conclusion still holds — but for a different reason, since there is no hook gate any more (A7). Every registered target participates, base-declared hook or not | CONFORMS (conclusion) / STALE-DESCRIPTION (mechanism) |
| F17 | The helper is queryset-polymorphic: "it narrows whatever queryset it is handed ...; it never evaluates, never reorders, never projects — pure `.filter(...)` composition, so it composes with `only()` projection and ordering downstream" | Half true, and the false half is load-bearing. The root is now **sealed and rebuilt** before any narrowing (`permissions.py::apply_cascade_permissions` #"_prepared_visibility_source(" with `require_model_rows=False`, then `permissions.py::_validate_root_queryset`), so: a consumer `QuerySet` subclass is **not** returned, a **sliced** root is rejected, and a **combined** root is rejected. Measured directly during this review (temp test, `docs/builder/temp-tests/review-1a/test_polymorphic_bullet.py`): `isinstance(out, MyQS)` -> `False`, `type(out).__name__` -> `QuerySet`; `only("id","name")` survives (`deferred_loading` -> `({'name','id'}, False)`) and `order_by("name")` survives; a sliced root raises #"got a sliced queryset; the cascade narrows by .filt..."; a `union()` root raises #"got a union() combined queryset". Pinned in-tree by `::test_root_queryset_shape_rejections`, `::test_values_root_is_supported_input`, `::test_root_queryset_filter_override_is_neutralized_by_sealing`, `::test_unsealable_root_query_class_fails_closed_with_cascade_prose` | SUPERSEDED (`c68aecab` for the sliced/combined rejections; `60998b17` for the seal) |
| F18 | Sharded callers: alias propagation is per-handed-queryset; in the optimizer prefetch path the cascade pins to the child's own routed alias, citing `optimizer/walker.py::_build_child_queryset`, `walker.py:212` | The behaviour holds (the prefetch child *is* the root call there, so `state.alias` is its `.db`). The citation does not: `_build_child_queryset` is at `optimizer/walker.py:355`, and `walker.py:212` is inside `optimizer/walker.py::_graphql_names_by_python_name`. The raw `path:NN` form is also an `AGENTS.md` rule-27 violation in a standing doc | CONFORMS (behaviour) / STALE-DESCRIPTION (citation) |
| F19 | Re-entrancy / idempotence: calling the helper twice on the same queryset double-applies the same filters; harmless, documented, not guarded | Verified directly rather than assumed, because the root is now sealed and the second call's root carries an `__in` subquery in its `where` tree. Temp test `docs/builder/temp-tests/review-1a/test_reentrancy_idempotence.py`: the second application seals cleanly and the result set is unchanged (`["keeps"]` both times) | CONFORMS |
| F20 | `fields=` accepted-and-skipped names: a cascadable edge whose target "lacks a registered type **or custom hook**" validates fine and contributes nothing | B17 | SUPERSEDED |
| F21 | `fields=[]` is a defined no-op, distinct from `fields=None` | `permissions.py::_validate_fields` returns an empty set; `permissions.py::_walk` skips every edge. Pinned by `::test_fields_empty_list_cascades_nothing`. **Unstated new role**: `fields=[]` is now also the one permitted re-entrant shape and the documented cycle-breaking recourse (`permissions.py::apply_cascade_permissions` #"if names_to_walk == set():"), which the bullet does not mention | CONFORMS (no-op) / STALE-DESCRIPTION (incomplete) |

#### G. `## Definition of done` 1-5

| # | Contract (spec) | Evidence at `HEAD` | Grade |
|---|---|---|---|
| G1 | DoD 1: the spec is at `docs/spec-034-permissions-0_0_10.md`, with the `-terms.csv` companion, and `uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` reports `OK: <N> terms` | The path is stale twice over. Proven: the command as written exits **2** with `error: missing file: docs/spec-034-permissions-0_0_10.md`; at `docs/SPECS/spec-034-permissions-0_0_10.md` it reports `OK: 42 terms`, exit 0. The `-terms.csv` companion is at `docs/SPECS/appx/spec-034-permissions-0_0_10-terms.csv`. `### Decision 1` carries the same stale path in prose | STALE-DESCRIPTION |
| G2 | DoD 2: `permissions.py` ships `apply_cascade_permissions` with the Decision 5 walk (single-column forward scope, registry primary lookup, custom-hook gate, `Q(__in) | Q(__isnull)` intersection, `_default_manager`) | Ships, with the Decision-5 divergences of A2 / A4 / A5 / A7 / A8b folded in | CONFORMS (delivery) / SUPERSEDED (the enumerated walk) |
| G3 | DoD 3: the four upstream invariants are each pinned by a dedicated test | All four have a dedicated row (A18). The cycle-guard invariant is restated as fail-closed. The alias pin is `FAKESHOP_SHARDED`-gated and therefore does not run under a bare `uv run pytest` — but CI does run it: `.github/workflows/django.yml` #"FAKESHOP_SHARDED: ${{ matrix.fakeshop_sharded }}", and the spec's own Slice-1 harness note anticipates the gating | CONFORMS (invariant coverage) / SUPERSEDED (the cycle invariant's statement) |
| G4 | DoD 4: `fields=` validates loudly; the sync helper raises `SyncMisuseError` with the coroutine closed; `aapply` runs the walk through `sync_to_async(thread_sensitive=True)` | A13 / A14 / A15 / A16 | CONFORMS |
| G5 | DoD 5: both symbols exported from the package root, present in `__all__`, pinned by the grown exports test | A17 | CONFORMS |

### Test-name census

The spec's `## Test plan` `### Slice 1` names **23** tests. The list was re-derived from `docs/SPECS/spec-034-permissions-0_0_10.md` lines 374-394, not from the prompt's transcription; the transcription was accurate. Existence was measured with `grep -rho "<name>" --include='*.py' .` counting **occurrences**, not matching lines.

**16 of 23 exist verbatim.** Seven do not. **None of the seven is an unpinned contract.** Every one of the seven is a contract the spec still states but a later commit deliberately inverted, and in every case a test of the *inverted* contract exists under a new name — which is exactly the signature of a deliberate flip rather than a dropped test.

| Spec-named test | Occurrences at `HEAD` | Live pin | Verdict |
|---|---|---|---|
| `test_cycle_guard_contextvar_breaks_mutual_cascade` | 0 | `tests/test_permissions.py::test_mutual_cycle_fails_closed_with_path` (+ `::test_longer_cycle_renders_full_path`, `::test_cyclic_diamond_fails_closed`) | SUPERSEDED — the contract it pinned (break the cycle, return partially narrowed) is inverted; the inverted contract is pinned |
| `test_single_column_scope_skips_m2m_reverse_and_generic` | 1 | same name | CONFORMS |
| `test_mti_parent_link_edge_excluded` | 0 | `::test_mti_parent_link_edge_included` (+ three row-level MTI pins) | SUPERSEDED — name and contract both inverted |
| `test_multi_db_subquery_pinned_to_caller_alias` | 1 | same name, `FAKESHOP_SHARDED`-gated; passes under `FAKESHOP_SHARDED=1` | CONFORMS |
| `test_nullable_fk_rows_preserved` | 1 def (+1 prose mention) | same name | CONFORMS |
| `test_cascade_excludes_rows_with_hidden_targets` | 1 | same name | CONFORMS |
| `test_hidden_and_missing_targets_indistinguishable` | 1 | same name | CONFORMS |
| `test_transitive_cascade_two_deep` | 1 def (+1 prose mention) | same name | CONFORMS |
| `test_identity_hook_targets_skipped_no_sql` | 0 | `::test_identity_hook_targets_compose_default_manager` (+ `::test_proxy_target_filtered_default_manager_composes`) | SUPERSEDED — the skip is gone; the compose is pinned |
| `test_unregistered_target_model_skipped` | 1 | same name | CONFORMS |
| `test_secondary_type_never_cascade_target` | 1 | same name | CONFORMS |
| `test_secondary_type_as_root_reaches_primary_on_transitive_revisit` | 0 | `::test_secondary_root_self_edge_reaches_primary_then_fails_closed` | SUPERSEDED — the primary-resolution half is still pinned; the "walk terminates by returning" half is now "walk terminates by raising" |
| `test_cascade_target_sliced_or_values_queryset_is_consumer_bug` | 0 | `::test_hook_return_rejections_fail_closed`, `::test_hook_values_and_values_list_projections_are_normalized`, `::test_to_field_edge_compares_target_column` | SUPERSEDED — "consumer bug, not absorbed" became "validated, then normalized" |
| `test_fields_scopes_walk` | 1 | same name | CONFORMS |
| `test_fields_unknown_name_raises` | 1 | same name | CONFORMS |
| `test_fields_non_cascadable_name_raises` | 1 | same name | CONFORMS |
| `test_fields_valid_but_hookless_name_accepted` | 0 | `::test_fields_valid_but_unregistered_target_accepted` | RENAMED + narrowed — "hookless" targets no longer skip, so only the unregistered half survives; the surviving half is pinned under the new name |
| `test_fields_bare_string_raises` | 1 | same name | CONFORMS |
| `test_fields_empty_list_cascades_nothing` | 1 | same name | CONFORMS |
| `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` | 1 | same name | CONFORMS |
| `test_aapply_runs_walk_off_event_loop` | 1 | same name | CONFORMS |
| `test_aapply_async_target_hook_still_raises` | 1 | same name | CONFORMS |
| `test_self_referential_fk_cascades_once` | 0 | `::test_self_referential_cascading_hook_fails_closed` + `::test_self_referential_fields_scoping_breaks_recursion` | SUPERSEDED — "cascades once" became "fails closed, with `fields=[]` as the recourse" |

Plus the spec's final Slice-1 test-plan line, "Export pins in `tests/base/test_init.py`: both symbols importable from the package root and present in `__all__`" — CONFORMS, pinned by `tests/base/test_init.py::test_public_api_surface_is_pinned` and `::test_star_import_preserves_namespace_hygiene`.

**The highest-value finding this cohort could have produced — a test absent while the spec still states the contract it pinned — does not exist here.** Every absent name's contract was deliberately replaced, and the replacement is pinned. The spec is what is out of date.

### High:

None.

No contract in the R1a territory is stated by the spec, unsuperseded, and unimplemented. The five divergences the build plan flagged as "known-live", plus sixteen more this pass found, are all deliberate post-ship changes with named superseding commits, corroborated by `docs/README.md` already carrying the hardened contract. Nothing routes to R3 from this cohort.

### Medium:

#### M1 — `getattr(field, "is_relation", False)` is a fail-open default on the walk's fail-closed / skip decision

`django_strawberry_framework/permissions.py::_is_unsupported_forward_edge` (permissions.py:219) opens with `getattr(field, "is_relation", False)`. This is the catalogued **`getattr` default standing in for an attribute whose absence is meaningful** shape from `BUILD.md` `### Fail-open shapes`, sitting on the decision that separates "this forward relation cannot be composed, fail the walk closed" from "this is not a relation, skip it". An object reaching that predicate without an `is_relation` attribute is classified as *not a relation* and therefore silently skipped — the permit direction.

`BUILD.md` puts the floor at Medium for a fail-open shape on a decision path, so it is filed here. **No exploit path exists at `HEAD`**, and that is stated as a measurement, not a hope: the only caller is `permissions.py::_edge_plan`, whose sole input is `model._meta.get_fields()`, every member of which is a Django `Field` / `ForeignObjectRel` / `GenericForeignKey` and every one of those defines `is_relation` as a class attribute. Note the neighbouring predicates in the same expression (`field.many_to_many`, `field.one_to_many`) are read by plain attribute access and would raise, so this one `getattr` is also inconsistent with its own line.

Recommended change (R2/maintainer call, not a repair this cohort routes): read `field.is_relation` directly, matching the two predicates beside it, so a shape that cannot answer the question fails loudly instead of being classified as a non-relation.

#### M2 — `## Error shapes` omits ten of the twelve error surfaces the helper actually has

Census row C11. A consumer reading `## Error shapes` learns two of the twelve `ConfigurationError` shapes `apply_cascade_permissions` can raise, and the two it learns include one (`Cycles never raise`) that is now the opposite of the truth. Missing tests for important branches is not the problem — every one of the ten is pinned. The problem is that the spec's own error inventory is the surface a `0.1.x` consumer and the `0.0.11` mutations cohort read. Routes to R2.

#### M3 — `## Edge cases and constraints`' queryset-polymorphism bullet is false in the direction that breaks a consumer

Census row F17. "It narrows whatever queryset it is handed" now has three exceptions, two of which raise: a sliced root, a combined root, and a consumer `QuerySet` subclass (which is silently replaced by a plain framework-owned `QuerySet`). A consumer following the spec and passing `queryset[:100]` into the cookbook line gets a `ConfigurationError`; one whose `get_queryset` returns a custom `QuerySet` subclass gets a plain one back. Measured, not inferred (temp test output quoted in F17). Routes to R2.

### Low:

#### L1 — Decision 6's Consumer-recipe divergence cites a substring that no longer exists, on a premise that is no longer true

Census row B12. Two defects in one block: `types/resolvers.py::_make_relation_resolver #"return getattr(root, field_name)"` matches zero occurrences at `HEAD`, and the forward-FK branch now *does* re-check the target through its visibility hook (`types/resolvers.py::_visible_related_object`), which is precisely what the block asserts the package "deliberately did not port". `scripts/check_citations.py` cannot see this — it resolves `path::Symbol` citations in `.py` files and `KANBAN.md` only (its clean run reports `857 citations resolve (738 in 431 .py files, 119 in KANBAN.md)`), so a `path #"substring"` citation inside `docs/` has no gate at all. Routes to R2.

#### L2 — Two stale citations in surviving contract prose, one of them a rule-27 violation

Census rows F18 and G1: `optimizer/walker.py::_build_child_queryset, walker.py:212` (the symbol moved to walker.py:355; line 212 is now unrelated code; and the raw `path:NN` form is forbidden in a standing doc by `AGENTS.md` rule 27), and `docs/spec-034-permissions-0_0_10.md` as the spec's own path in `### Decision 1` and DoD item 1 (the file is archived at `docs/SPECS/`; the DoD's `--spec` argument exits 2 as written). Routes to R2.

#### L3 — Decision 3's module-contents inventory omits the `SyncMisuseError` re-export

Census row B2. Cosmetic; the re-export is argued for in place and adds no new name to the package-root `__all__`. Routes to R2.

### DRY findings

#### D1 — `_cascadable_edges` and `_cascadable_edge_names` are a two-level indirection with zero production readers (existence challenge)

`django_strawberry_framework/permissions.py::_cascadable_edges` (permissions.py:248) has exactly **one** reader in the whole tree: `permissions.py::_cascadable_edge_names` (permissions.py:253). `_cascadable_edge_names` has **zero** production readers — its only call sites are `tests/test_permissions.py:527`, `:681`, `:798`. Measured:

```
grep -rn "_cascadable_edges" --include='*.py' .   -> 2 hits: the def, and the one call inside _cascadable_edge_names
grep -rn "_cascadable_edge_names" --include='*.py' . -> 5 hits: the def, one test import, three test call sites
```

Every production path — `permissions.py::_validate_fields`, `permissions.py::apply_cascade_permissions`'s preflight, and `permissions.py::_walk` — reaches for `_edge_plan(model)` directly and never goes through either wrapper. So the pair exists solely as a test-facing convenience, and `_cascadable_edges` exists solely to feed `_cascadable_edge_names`. `_cascadable_edges` is deletable outright by inlining `_edge_plan(model).cascadable` into its single caller; whether `_cascadable_edge_names` should survive as a deliberate test seam is a maintainer call, and it is a small, harmless one.

Per `worker-3.md` `### The existence challenge` this is raised, not decided, and it is escalated below rather than held against acceptance.

#### D2 — no duplication findings in the helper itself

The static helper's repeated-string-literal section reports five repeats, all of them message-prose fragments in the two error renderers and the validators: `apply_cascade_permissions for` (4x), `apply_cascade_permissions fields=` (2x), `.get_queryset returned a` (2x), `) for the cascade subquery on` (2x), `; a cascade cannot compose cross-database subqueries.` (2x). Each occurrence sits inside a distinct f-string whose surrounding sentence differs, and the two `cross-database subqueries` sites are genuinely two different errors (a nested application on a divergent alias, in `apply_cascade_permissions`; a hook return on a divergent alias, in `_edge_error_renderer`). Extracting a shared fragment constant here would make each message harder to read at its site and would couple two independent errors. No finding.

The larger DRY story in this module is already resolved in the right direction: `c68aecab` + `60998b17` moved the hook-result shape / concrete-table / alias contract out of `permissions.py` and into the one shared sealed boundary in `utils/querysets.py`, leaving only the SQL-composability battery around the `.values(...)` re-projection cascade-local, which is the half with no boundary analogue. That is the correct seam.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list are unchanged by this cohort (which writes no source at all).

The card's two names are present and pinned:

- `django_strawberry_framework/__init__.py` #"from .permissions import" imports `aapply_cascade_permissions` and `apply_cascade_permissions`.
- `__init__.py::__all__` carries `"aapply_cascade_permissions"` and `"apply_cascade_permissions"`.
- `tests/base/test_init.py::test_public_api_surface_is_pinned` asserts the whole `__all__` tuple by equality — both names appear in it — so a silent widening or removal fails at test time. `::test_star_import_preserves_namespace_hygiene` additionally proves every `__all__` name is bound by `from django_strawberry_framework import *`, which is the DoD's "`from django_strawberry_framework import apply_cascade_permissions` works" in its strongest form.

**The `SyncMisuseError` re-export in `permissions.py` adds no public name.** `permissions.py #"from .utils.querysets import SyncMisuseError as SyncMisuseError"` is the redundant-alias re-export form; `SyncMisuseError` is already in the package-root `__all__`, sourced from `.types` (`__init__.py` #"from .types import DjangoType, SyncMisuseError, finalize_django_types"), and `tests/base/test_init.py::test_reexported_types_resolve_to_canonical_subpackage_definitions` pins that root binding to `django_strawberry_framework.types`'s. The `permissions.py` re-export therefore widens the *module's* import surface (`from django_strawberry_framework.permissions import SyncMisuseError` works, and `tests/test_permissions.py` uses exactly that import) without widening the package's. No spec authorization is needed because the package surface is unchanged; the only spec consequence is census row B2.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (This cohort writes one file, its own artifact.)

### Static inspection helper

Run: `uv run python scripts/review_inspect.py django_strawberry_framework/permissions.py --output-dir docs/shadow`. Output: `docs/shadow/django_strawberry_framework__permissions.overview.md` and `.stripped.py`. No skip. Line numbers below are the original source's, per `BUILD.md` `### Output files, and why their line numbers are NOT canonical`.

**Django / ORM markers — all 10 walked, one line each.**

| Marker | Justification or finding |
|---|---|
| permissions.py:240 `_meta` in `for field in model._meta.get_fields():` (`_edge_plan`) | Justified and load-bearing. `_meta.get_fields()` is the authoritative model-edge list, and reading it rather than the type's *selected* fields is what makes census row F10 (`Meta.fields`-excluded edges still cascade) true. Immutable after app loading, which is what licenses the `lru_cache` on the enclosing function. |
| permissions.py:371, 457, 459 `QuerySet` (`_validate_root_queryset`, `_validated_target_subquery` param + return) | Type annotations on the two validators. No behavior. |
| permissions.py:558, 561 `QuerySet` (`apply_cascade_permissions` params) | Public signature annotations, matching Decision 4 exactly. |
| permissions.py:673, 677 `QuerySet` (`_walk` params) | Private helper annotations. |
| permissions.py:721, 724 `QuerySet` (`aapply_cascade_permissions` params) | Public async signature, matching Decision 4. |

No ORM marker is a finding. Notably absent from this section — and worth saying because its absence is the evidence — is any direct `.objects` use: the walk seeds from `_default_manager` (Decision 5 step 4), which the helper's marker scan would have surfaced had it drifted.

**Repeated string literals (5).** Walked under `### DRY findings` D2. No finding.

**Control-flow hotspots (6).** Medium-tier complexity attention applied to each:

| Hotspot | Assessment |
|---|---|
| `_validate_fields` — 65 lines, 7 branch nodes | Each branch is one distinct rejection with its own message (bare string, non-iterable, non-string entries, unsupported forward relation, unknown/non-cascadable) plus the `None` short-circuit. Flattening would merge messages that name different mistakes. No finding. |
| `_root_error_renderer` — 44 lines, **0** branch nodes | The count is the closure, not the rendered branches; the inner `_render` has three. The trailing branch is deliberately unconditional and commented as such (permissions.py:356-359), which is the right choice: a future boundary code would otherwise fall through silently. Verified the claimed reachable code set is exactly `type` / `table` / `untrusted` by reading `utils/querysets.py::_seal_or_defect` — `sliced` and `projection` are emitted only under `require_model_rows`, and the cascade passes `False`, so no code can reach the trailing branch mislabelled. No finding. |
| `_edge_error_renderer` — 53 lines, 0 branch nodes | Same shape, same verification (permissions.py:441-444); reachable set is `type` / `table` / `untrusted` / `alias`. No finding. |
| `_validated_target_subquery` — 89 lines, 7 branch nodes | Five independent rejections plus the alias-shadow disjunction, each guarding a different way `.values(attname)` would change semantics rather than projection. This is the module's security core and the branches are not collapsible. Failability-proved below. No finding. |
| `apply_cascade_permissions` — 112 lines, 7 branch nodes | Seal, root validation, `fields=` resolution, unsupported-edge preflight, state install vs. nested, alias divergence, cycle-vs-`fields=[]`. Long, but each step must precede the next (the preflight must fire before any hook; the alias check must fire before the cycle check so a cross-DB nested call is not masked by a cycle error). No finding. |
| `_walk` — 47 lines, 6 branch nodes | The per-edge loop: scope filter, registry miss, per-edge frame, nullable disjunct. No finding. |

**Imports (12).** Ten standard/Django, two local-package groups. One cross-folder import to weigh: `from .utils.querysets import (_prepared_visibility_source, apply_type_visibility_sync, model_for, run_in_one_sync_boundary)` — a root module importing four names from a subpackage, one of them private. This is a structural change worth flagging and it is the *right* one: `utils/querysets.py::run_in_one_sync_boundary`'s own docstring records that it lives in `utils/` as a "neutral home ... so read-side modules (`filters/`, `orders/`, root `permissions.py`) can reuse it without a root-into-subpackage import" — i.e. the direction is deliberate and the alternative (duplicating the sealed boundary in `permissions.py`) is the DRY violation this replaced. The private `_prepared_visibility_source` import is the one wart; it is the source-side twin of the public `apply_type_visibility_sync` and has no public alias, which is a `utils/querysets.py` naming question outside this cohort's territory. Noted for Worker 1, not filed as a finding. No import creates a cycle: `permissions.py` -> `utils/`, `exceptions`, `registry` only.

### Failability proofs

`BUILD.md` `### Who performs it` assigns the record to Worker 2 and the audit plus a re-run subset to Worker 3. **There is no Worker 2 record to audit here** — this cohort has no build pass and no diff, so the mandatory re-run floor ("every boundary whose *recorded* failing-row count is 3 or fewer") has an empty input and an empty re-run set would be legal.

It is not empty. Two boundaries in this territory gate visibility directly, and a conformance audit that graded the divergence class SUPERSEDED without proving the replacement contract is actually pinned would be grading prose. Both were proved, one at a time, through `scripts/prove_failability.py` (which enforces `BUILD.md`'s ordering: anchor-check before the pre-mutation copy, scratch root outside the repo, no `git`, restore proved by byte comparison). Manifest: `docs/builder/temp-tests/review-1a/proofs.json`; full report: `docs/builder/temp-tests/review-1a/proofs-report.md`. Scratch root: outside the repository, under this session's scratchpad. Run exit code **0** (every entry proved, none weakly pinned, no collection/setup errors).

Anchor pre-check (`--check-anchors-only`) passed for both entries before any mutation: each anchor matched exactly once, which is also the evidence the tree carried no prior live mutation.

- **`django_strawberry_framework/permissions.py::_validated_target_subquery #"alias shadows"`** — mutation applied: `if attname in target_qs.query.annotations or attname in target_qs.query.extra:` -> `if False:`, making the annotation / extra-select alias-shadow rejection unreachable so a hook return whose `annotate(...)` alias shadows the edge's target column re-projects to the injected constant. Scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_permissions.py`. Pre-mutation state of that scope: `63 passed, 1 skipped`, pytest exit 0; pre-existing failing rows excluded from the count: 0. Failing node ids (count is `len()` of this list = **3**):
  - `tests/test_permissions.py::test_annotation_alias_shadow_cannot_bypass_visibility`
  - `tests/test_permissions.py::test_annotation_alias_shadow_to_field_cannot_bypass_visibility`
  - `tests/test_permissions.py::test_hook_return_rejections_fail_closed`

  Collection/setup errors: **0**. Revert proved by byte comparison: `filecmp.cmp(shallow=False)` True; sha256 `d22a5ed78aca45dd...` == `d22a5ed78aca45dd...` against the pre-mutation copy. Not weakly pinned (3 > 1); at the re-run floor exactly, which is why it was chosen.

- **`django_strawberry_framework/permissions.py::apply_cascade_permissions #"raise _cycle_error"`** — mutation applied: `raise _cycle_error(state, cls)` -> `return queryset`, i.e. the boundary is replaced by **the pre-hardening `spec-034` contract itself** (re-entry returns the partially-narrowed queryset). Scope as run: identical. Pre-mutation state of that scope: `63 passed, 1 skipped`, pytest exit 0; pre-existing failing rows excluded: 0. Failing node ids (count is `len()` = **5**):
  - `tests/test_permissions.py::test_mutual_cycle_fails_closed_with_path`
  - `tests/test_permissions.py::test_longer_cycle_renders_full_path`
  - `tests/test_permissions.py::test_cyclic_diamond_fails_closed`
  - `tests/test_permissions.py::test_secondary_root_self_edge_reaches_primary_then_fails_closed`
  - `tests/test_permissions.py::test_self_referential_cascading_hook_fails_closed`

  Collection/setup errors: **0**. Revert proved by byte comparison, same command and result as above.

This second proof is the evidentiary heart of the census: reverting `HEAD` to the contract the spec still states fails five rows. The spec's cycle sentence is not merely out of date, it is actively contradicted by the suite, which is what makes the SUPERSEDED grade a measurement rather than an inference.

Post-run tree check: `grep -c "if attname in target_qs.query.annotations or attname in target_qs.query.extra:" django_strawberry_framework/permissions.py` -> 1; `grep -c "            raise _cycle_error(state, cls)" ...` -> 1; `grep -c "if False:" ...` -> 0; `git diff --stat -- django_strawberry_framework/permissions.py` -> empty; no `ACTIVE-MUTATION.json` in the scratch root. **No mutation survives this pass.**

Boundaries accepted without an independent re-run, and why: every other rejection path in `permissions.py` (`_validate_fields`'s five, `_validate_root_queryset`'s two, `_validated_target_subquery`'s other four, the unsupported-edge preflight, the nested-alias divergence check, and the four `_edge_error_renderer` / three `_root_error_renderer` codes) is named by a `tests/test_permissions.py` row read in this pass and is not on the mandatory floor (no Worker 2 record places any of them at <= 3 rows, and none was distrusted on reading). The two chosen are the two the divergence class turns on.

### Hot-path budget

Not applicable; the build plan declares R1 lands no source and no hot path. (`build-034-permissions-0_0_10.md` `Hot-path declaration`: "R1 and R2 land no source and declare none.")

### Floor verification

Not applicable; the build plan declares floor-verification scope `none` for R1. The floor itself, if a later pass needs it, is stated canonically in `docs/builder/BUILD.md` `## Floor verification` and is not restated here.

### What looks solid

- **The hardening is genuinely fail-closed, and it is pinned.** Both proved boundaries fail 3 and 5 rows respectively with zero collection errors. The suite would notice if either were removed.
- **The five known-live divergences were all reversals with a stated security reason, not drift.** The most striking is the identity-hook one: the spec's rationale companion records "calling every target's `get_queryset` unconditionally" as a *rejected alternative*, and `c68aecab` adopted it anyway — because a registered proxy type's filtered `_default_manager` **is** its visibility policy, and the old skip bypassed it. That is the rejected alternative being right for a reason the original deliberation did not have. R2 should record it that way.
- **The `.values(target_field.attname)` re-projection is a strictly better contract than the one the spec ships.** The spec's F15 bullet documents four ways a consumer hook's return silently narrows on the wrong column and calls each one "a consumer bug". `HEAD` makes three of them impossible and rejects the fourth. `::test_to_field_edge_compares_target_column` pins the case the old contract got wrong even for a well-behaved hook.
- **The delegation to the shared sealed boundary is the right seam.** `permissions.py` keeps exactly what has no analogue elsewhere (the SQL-composability battery around the re-projection) and hands the shape / table / alias contract to the one place that owns it, with its own prose preserved through the two `render_error` seams. Both renderers' "unhandled future code falls through" comments are correct, and I verified their claimed reachable code sets against `utils/querysets.py::_seal_or_defect` rather than accepting them.
- **The multi-DB invariant is gated where it counts.** It is skipped locally and green in CI (`.github/workflows/django.yml` runs a `FAKESHOP_SHARDED` matrix axis), and the spec's own harness note anticipated exactly this. The pin observes the alias *inside the hook* (`received_dbs == ["shard_b"]`) rather than reconstructing it in the assertion, which is what makes it a real pin.
- **The traversal-state isolation has a suite-wide tripwire.** `tests/test_permissions.py::_assert_contextvar_clean` is autouse and asserts `_cascade_state.get() is None` after every test, so a leaked frame is a hard failure in whichever test leaked it rather than a flake in the next one.

### Temp test verification

Three temp artifacts under `docs/builder/temp-tests/review-1a/` (gitignored):

- `test_reentrancy_idempotence.py` — written to test the `## Edge cases` re-entrancy/idempotence bullet against the sealed root, because the second application's root carries an `__in` subquery in its `where` tree and the bullet predates the seal. Result: the bullet holds (`["keeps"]` both applications). **Disposition: no promotion needed** — it confirmed an existing contract rather than catching a bug, and the underlying seal behavior is already pinned by `::test_root_queryset_filter_override_is_neutralized_by_sealing`. **Deleted at the end of this pass.**
- `test_polymorphic_bullet.py` — written to measure the three exceptions to the queryset-polymorphism bullet rather than infer them from the seal's docstring. Result quoted verbatim in census row F17 and finding M3. **Disposition: no promotion needed** — all three behaviors are already pinned in-tree (`::test_root_queryset_shape_rejections`, `::test_values_root_is_supported_input`, `::test_root_queryset_filter_override_is_neutralized_by_sealing`); the temp test measured them together to write one finding. **Deleted at the end of this pass.**
- `proofs.json` + `proofs-report.md` — the failability-proof manifest and its machine-emitted report, at the manifest home `BUILD.md` `### Mechanized` names. Kept for the cycle; cleared by `scripts/clean_up.py`.

No temp test caught a real bug, so nothing is escalated to Worker 2 for promotion.

### Notes for Worker 1 (spec reconciliation)

Every bullet is one spec sentence R2 must rewrite: what it says, what is true at `HEAD`, and the attribution R2 needs for the rationale companion's `**Post-ship:**` bullet. Ordered by owning Decision so R2 can walk the companion top to bottom.

**Decision 1 / DoD 1**

- `### Decision 1` — "The spec file lives at **`docs/spec-034-permissions-0_0_10.md`**". True at `HEAD`: `docs/SPECS/spec-034-permissions-0_0_10.md`. DoD item 1 repeats the path twice, once inside the `--spec` argument of a command whose exit code is load-bearing; run as written it exits 2 (`error: missing file`), and at the archived path it reports `OK: 42 terms`. Attribution: the standing spec-archival sweep (`AGENTS.md` rule 26 / `docs/SPECS/NEXT.md` Step 8), not a code change. Slice 0 flagged this unverified; it is now verified.

**Decision 3**

- `### Decision 3` — "Contents: the two public functions, the module-level `ContextVar`, and the private walk/validation helpers." True at `HEAD`: plus a re-export, `permissions.py #"from .utils.querysets import SyncMisuseError as SyncMisuseError"`, which makes the cascade's error surface importable from the module without reaching into `utils/` and adds no package-root name. Attribution: `c68aecab`.

**Decision 5** — the largest cluster; five separate sentences.

- `### Decision 5` step 1 — the three-predicate scope test (`related_model` present AND `getattr(field, "column", None) is not None` AND NOT `parent_link`), with the whole Django-6.0 `hasattr`-correction paragraph that justifies the second predicate. True at `HEAD`: `permissions.py::_is_cascadable_edge` is `isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None`. The `isinstance` test subsumes the `related_model` predicate and makes the M2M / `GenericRelation` `column`-value argument moot (neither is a `ForeignKey`); the `column` check survives only as a guard against a future non-single-column `ForeignKey` shape. Attribution: `c68aecab`. **The Slice 0 note about "the pinned Django 6.0" being a stale present-tense claim resolves here**: the sentence it appears in is being rewritten anyway.
- `### Decision 5` step 1's `parent_link` clause, the `## Slice checklist` Slice 1 bullet's "and the MTI `<parent>_ptr` edge precisely", the `## Edge cases` bullet **Multi-table-inheritance parent link — excluded by design** (including its *Deferred extension* paragraph), and the `## Test plan` name `test_mti_parent_link_edge_excluded`. True at `HEAD`: MTI parent links **cascade** — a child row whose MTI parent is hidden drops. Attribution: `c68aecab`, whose message states it and whose reason is that the exclusion left a hidden parent reachable through its child type. The "deferred opt-in extension" shipped as the default.
- `### Decision 5` step 3 (the `has_custom_get_queryset()` hook gate, "the edge is skipped with zero SQL emitted"), the matching clause in the `## Slice checklist`, `### Explicitly do not borrow`'s "**The unconditional target call**" bullet, the parity-table row, `## Goals` 1, and `## Definition of done` item 2. True at `HEAD`: **every registered target composes** its `_default_manager` subquery, identity hooks included; only an unregistered target model is outside the visibility contract. Attribution: `c68aecab`. **R2 must record this as a reversal of a recorded rejected alternative** — the rationale companion's Decision 5 rejects "calling every target's `get_queryset` unconditionally" on dead-SQL grounds; the reversal's reason is different and security-shaped (a registered proxy type's filtered `_default_manager` *is* its visibility policy, and the skip silently bypassed it), so the `**Post-ship:**` bullet should say the alternative was re-adopted for a reason the original deliberation did not weigh, not that it was wrong to reject.
- `### Decision 5` step 4's constraint expression `Q(**{f"{field.name}__in": target_qs}) | Q(**{f"{field.name}__isnull": True})`, the same expression in the `## Slice checklist`, and `## Definition of done` item 2. True at `HEAD`: the `__isnull` disjunct composes **only when `field.null`** (`permissions.py::_walk` #"if field.null:"). Nullable-FK preservation is unaffected. Attribution: `c68aecab`.
- `### Decision 5` step 5 — "re-entry on a `cls` already in the set returns the queryset unchanged (partial narrow, never a raise)". True at `HEAD`: re-entry raises a path-rich `ConfigurationError` rendering the edge path (`AType.b -> BType.a -> AType`). Attribution: `c68aecab`; its stated reason is that a silently-broken cycle skips the re-entered type's *outgoing* visibility edges, so a root row whose hidden relation was only reachable through the re-entry survives. **This same sentence also appears in `## Goals` 1 ("partial-narrow on cycle break, never a raise"), `### Error shapes` ("Cycles never raise"), the `## Slice checklist` Slice 1 cycle bullet, the `## Edge cases` self-referential-FK and mutual-cascade-A<->B bullets, the parity table's "ContextVar cycle guard" cell, and the secondary-type-as-root bullet's termination clause** — eight sites, three grammars (`never a raise`, `partially-narrowed`, `partial narrow`). Occurrence counts in the spec, measured: `never a raise` 2, `partially-narrowed` 3, `partial narrow` 1, `seen-set` 16. A grep for any one of those spellings misses the others.
- `### Decision 5` step 5 and every "seen-set" site (16 occurrences) — the mechanism is a module-level `ContextVar` holding a **frozen `_TraversalState`** (root alias, active-type tuple, edge-path frames), named `_cascade_state`, not a seen-set named after upstream's `_cascade_seen`. `_cascade_seen` appears once in the spec and zero times in the source. The `## Slice checklist`'s "the upstream `_cascade_seen` shape verbatim" is the sharpest instance. Attribution: `c68aecab`.

**Decision 6**

- `### Decision 6`'s **Consumer-recipe divergence** block — the citation `django_strawberry_framework/types/resolvers.py::_make_relation_resolver #"return getattr(root, field_name)"` matches **zero** occurrences at `HEAD`, and the premise it supports ("reads the forward FK by bare accessor with no `DoesNotExist` / sentinel fallback") is false: the forward-FK branch reads `getattr(root, accessor_name)` and routes it through `types/resolvers.py::_visible_related_object` whenever `types/resolvers.py::_custom_visibility_type` resolves a target type with a custom hook, so a hidden forward-FK target now resolves to `None` at the field. The block's *conclusion* about the fakeshop hooks may still hold — R1c owns `examples/fakeshop/apps/products/schema.py` — but R2 must not leave the reason standing. Attribution: the per-relation visibility work in `types/resolvers.py` (outside this cohort's source territory; R2 should date it from `git log --follow django_strawberry_framework/types/resolvers.py`). Note no gate can see this: `scripts/check_citations.py` resolves `path::Symbol` in `.py` files and `KANBAN.md` only.

**Decision 8**

- `### Decision 8` and the `## Edge cases` **Sharded callers** bullet — the behaviour is unchanged and correct, but two things are missing and one citation is wrong. Missing: a nested cascade application whose queryset runs on a different alias now **fails closed** (`permissions.py::apply_cascade_permissions` #"nested walk for"), and a hook return explicitly routed off the root alias fails closed while an *unrouted* one is repinned onto it (the sealed boundary's alias contract). Wrong: `optimizer/walker.py::_build_child_queryset` is cited with `walker.py:212`; the symbol is at `optimizer/walker.py:355` and line 212 is inside `optimizer/walker.py::_graphql_names_by_python_name`. The raw `path:NN` form additionally violates `AGENTS.md` rule 27 in a standing doc. Attribution: `c68aecab` (nested-alias check) and `60998b17` (repin/reject) for the behaviour; ordinary code movement for the citation.

**Decision 9**

- `### Decision 9`'s "A name whose edge is cascadable but whose target has **no registered type or no custom hook** is accepted and skipped", and the matching `## Edge cases` bullet **`fields=` accepted-and-skipped names**. True at `HEAD`: only the no-registered-type half. A hookless registered target composes. Attribution: `c68aecab`. Live test name: `::test_fields_valid_but_unregistered_target_accepted`.
- `### Decision 9` and `### Error shapes` — a `fields=` name naming an **unsupported forward relation** (`GenericForeignKey` / composite) raises a *dedicated* error distinct from the not-cascadable one, naming the backing-FK recourse (`permissions.py::_validate_fields` #"have no single-column cascade semantics"). The spec has no sentence for this shape. Attribution: `c68aecab`.
- `### Error shapes` — the non-iterable / non-string-entry `fields=` cases (`_validate_fields`) are absent from the section. Slice 0 flagged this as a suspicion from the Revision 8 record; **confirmed**. Attribution: the change is recorded in the companion's Decision 9 `### Changes this Decision underwent` Revision 8 bullet, so this one is a pre-ship gap in `## Error shapes`, not a post-ship divergence — R2 should fix the section, not add a `**Post-ship:**` bullet for it.

**Decision 10**

- `### Decision 10` bullet 1 and `### Error shapes` — the `SyncMisuseError` message "point[s] the consumer at `aapply_cascade_permissions` or a sync hook rewrite". True at `HEAD`: the message says neither variant can await an async hook, and names **a sync hook rewrite or `fields=` scoping** (`permissions.py #"_ASYNC_RECOURSE"`), which `::test_sync_helper_raises_syncmisuseerror_on_async_target_hook` asserts positively *and* asserts the Relay wording absent. Decision 10's own **third** bullet already states this, so the spec currently contradicts itself; R2 should reconcile bullet 1 and `## Error shapes` to bullet 3. Attribution: `c68aecab`.
- `### Decision 10` bullet 1 — "each target-hook invocation is probed with the `utils/querysets.py::apply_type_visibility_sync` **shape** — `inspect.iscoroutine(result)`". True at `HEAD`: the cascade **delegates the whole invocation** to `apply_type_visibility_sync` (with `async_recourse=`, `render_error=`, `require_model_rows=False`), and the guard tests `inspect.isawaitable`, so any awaitable is rejected and futures are cancelled as well as coroutines closed (`utils/querysets.py::reject_async_in_sync_context` / `::_dispose_sync_awaitable`). Attribution: `60998b17` (`spec-045`) for the delegation.
- `### Decision 10` bullet 2 and the `## Slice checklist` — "`sync_to_async(thread_sensitive=True)`-wrapped execution of the sync walk (the `filters/sets.py` precedent)". True at `HEAD`: the wrap is `utils/querysets.py::run_in_one_sync_boundary`, the shared one-boundary primitive (its docstring cites `spec-040 D17` and names root `permissions.py` as an intended caller). Semantics identical; the named precedent is superseded by the shared primitive. Attribution: `spec-040` D17's one-boundary consolidation.

**Sections with no single owning Decision** (route to the companion's `## Non-Decision deliberation`)

- `### Error shapes` is materially incomplete: ten further `ConfigurationError` shapes exist at `HEAD` and are enumerated in census row C11. R2 should rewrite the section as the helper's actual error inventory.
- `## Edge cases and constraints`, **Cascade-target hook return contract** — "the cascade does not defensively rewrite the hook's return (a hook returning a non-row queryset is a consumer bug ... not silently absorbed)". True at `HEAD`: returns are validated and normalized. Sliced, combined, field-`distinct(...)`, grouped, and target-column-shadowing (`annotate` / `extra(select=...)`) returns each fail closed with their own message; everything accepted is re-projected to `.values(field.target_field.attname)`. The bullet's four worked examples are now all wrong: a `.values("col")` return is re-projected rather than silently mis-comparing, and a multi-column `.values()` no longer raises `ValueError`. Attribution: `c68aecab` (the battery and re-projection), `90d1cf14` (the annotation-alias shadow guard — note its own security argument: Django blocks a bare `annotate(id=Value(pk))` but permits `values("x").annotate(id=Value(pk))`, which would otherwise re-project to the injected constant and let a row pointing at a hidden target survive), `60998b17` (the shape/table/alias half moving to the shared boundary).
- `## Edge cases and constraints`, **The helper is queryset-polymorphic** — "narrows whatever queryset it is handed ...; never evaluates, never reorders, never projects — pure `.filter(...)` composition". True at `HEAD`: the root is sealed and **rebuilt** first, so a consumer `QuerySet` subclass is replaced by a framework-owned plain `QuerySet`, a **sliced** root is rejected, and a **combined** root is rejected. `only()` projection and downstream ordering do survive. Measured this pass (see census F17). Attribution: `60998b17` (the seal), `c68aecab` (`_validate_root_queryset`'s sliced/combined rejections).
- `## Edge cases and constraints`, **`GenericForeignKey` / `GenericRelation`** and **Composite-PK / composite-FK targets** — both say "excluded / skipped by the scope test". True at `HEAD`: `GenericRelation` is still skipped; the **GFK and composite / multi-column forward relations preflight the whole walk closed** (`fields=None` over a model carrying one raises before any hook runs; naming one in `fields=` raises at validation; the GFK's backing `content_type` FK stays selectable). Attribution: `c68aecab`, whose reason is that silently skipping such an edge would let a row pointing at a hidden target survive.
- `## Edge cases and constraints`, **`fields=[]` (empty iterable) is a defined no-op** — still true, but incomplete: `fields=[]` is now additionally **the one permitted re-entrant shape** and the documented recourse for a recursive graph. R2 should fold that role in when it rewrites the cycle contract, so the two sentences do not have to be read together to learn it.
- `## Edge cases and constraints`, **Abstract-base hooks** — the conclusion holds but the mechanism is gone: with no hook gate, every registered target participates regardless of where its hook is declared. Attribution: `c68aecab`.
- `## Edge cases and constraints`, **A secondary type as the root** — the primary-resolution semantics hold; "the walk still terminates (the primary lands in the set on its own first visit)" is now "the walk terminates by raising the path-rich cycle error". Live pin: `::test_secondary_root_self_edge_reaches_primary_then_fails_closed`, which asserts the exact path string. Attribution: `c68aecab`.
- `## Current state`, first bullet — Slice 0 flagged its last clause ("The four products-schema hooks that call it remain comments") as a present-tense sentence the same file's `Status:` line falsifies. **Confirmed as a stale-sentence shape from this cohort's side** (the module it describes shipped and every one of its contracts is live), but the hooks themselves are `examples/fakeshop/apps/products/schema.py` — R1c's territory. Flagged, not audited.
- **Neither `## Current state` nor any Decision mentions the sealed visibility boundary at all.** `spec-034` predates `spec-045`; `HEAD`'s `permissions.py` module docstring devotes four of its eight contract bullets to it. R2 will need a home for the source-side statement (root sealing, `require_model_rows=False`, the two `render_error` seams) — most naturally Decision 5 step 4 and Decision 10 bullet 1, with the history in the companion.

**Escalated: DRY existence challenge** (`worker-3.md` `### The existence challenge` — raised, not decided; not held against acceptance)

- `Escalated:` `django_strawberry_framework/permissions.py::_cascadable_edges` has exactly one reader, `::_cascadable_edge_names`, which itself has **zero** production readers — its three call sites are all in `tests/test_permissions.py`. Every production path calls `_edge_plan(model)` directly. Resolution paths for the maintainer: **(a)** delete `_cascadable_edges` and inline `_edge_plan(model).cascadable` into `_cascadable_edge_names`, keeping the latter as a deliberate test seam; **(b)** delete both and have the three test sites read `_edge_plan(model).cascadable` directly, as `tests/test_permissions.py:526` already does for the plan itself; **(c)** keep both as documented test seams. What would break under (b): three assertions change shape, nothing else — no production call site exists. This is a maintainability question, not a defect; it is Low-value work and should not gate anything.

**Escalated: fail-open shape with no live exploit path**

- `Escalated:` finding M1 — `permissions.py::_is_unsupported_forward_edge` #"getattr(field, \"is_relation\", False)" is the catalogued `getattr`-default fail-open shape on the walk's fail-closed-vs-skip decision, filed Medium per `BUILD.md`'s floor. It is unreachable at `HEAD` (the only input population is `model._meta.get_fields()`, every member of which defines `is_relation`), and the two predicates beside it on the same line use plain attribute access. Resolution paths: **(a)** read `field.is_relation` directly so an unanswerable shape raises rather than being classified a non-relation; **(b)** leave it and record the closed-population argument in the docstring so a later reader does not "fix" it into a real fallback. Either is defensible; (a) is one character-class of change and makes the line internally consistent.

**Out of territory, one bullet each, not audited**

- R1b: `### Decision 12` cites `optimizer/walker.py::_build_child_queryset` with `(walker.py:212-214)`. Same root cause as the `## Edge cases` Sharded-callers citation above — the symbol is at `optimizer/walker.py:355`, and line 212 is inside `::_graphql_names_by_python_name`.
- R1c: DoD item 13 / `### Decision 13` state that `__version__` and `tests/base/test_init.py::test_version` are unchanged by this card. At `HEAD` both read `0.0.14`, four patch lines past the `0.0.10` this card shipped in, which is expected but means the DoD sentence needs a tense R2 and R1c agree on.
- R1c: the Slice 0 note's card-id rot (`TODO-BETA-046-0.1.1` vs `docs/SPECS/spec-055-fieldset-0_1_1.md`; `TODO-ALPHA-035-0.0.10` vs the header's `DONE-035-0.0.10`; `TODO-ALPHA-034-0.0.10` vs `DONE-034-0.0.10`) touches Decisions 2, 6 and 13 and `## Out of scope`. Decision 6's `TODO-BETA-046-0.1.1` reference sits inside the Consumer-recipe divergence block this cohort is already asking R2 to rewrite, so the two edits collide — worth sequencing.
- General: `utils/querysets.py::_seal_or_defect`'s docstring says "The cascade (`require_model_rows=False`) keeps its own slice rejection in `permissions.py::_validated_target_subquery`". That is true for the *hook return*; the **root** slice rejection lives in `permissions.py::_validate_root_queryset`. A one-clause docstring imprecision in a file outside this cohort's source territory.

### Review outcome

`review-accepted`.

The audit is complete and its findings are recorded with their evidence. Nothing blocks the audit's own trustworthiness: the focused suite is green, both failability proofs are strongly pinned with proved reverts and zero collection errors, the tree carries no mutation from this pass, and every SUPERSEDED grade names a commit that landed after `0.0.10` and is corroborated by `docs/README.md`'s already-updated prose.

Findings M1, M2, M3, L1, L2, L3 and DRY D1 are recorded above and escalated to Worker 1 under `### Notes for Worker 1 (spec reconciliation)`; per `build-034-permissions-0_0_10.md`'s grading rule, disposition of every SUPERSEDED / STALE-DESCRIPTION / RENAMED row belongs to R2, and M1 plus DRY D1 are maintainer calls routed through Worker 1. **R3 (code repair) has no input from this cohort** — its conditional checklist box can be struck on R1a's account, subject to R1b and R1c.

---

## Final verification (Worker 1)

Performed by the R2 spec-reconciliation pass (`docs/builder/bld-034-review-2-spec_reconciliation.md`). Appended only; nothing this cohort wrote was altered.

**The census is sound.** Re-derived rather than accepted: the 88-row contract census and the 24-row test-name census re-tally to the totals stated (62 / 29 / 11 / 0 / **0 SKIPPED**, with 13 split rows and one three-grade row accounting for the middle column summing to 102), and the grading rule the build plan sets was applied consistently — every SUPERSEDED row names a commit that landed *after* the `0.0.10` ship, and the attribution section names five such commits with `git log` evidence. The three claims most worth distrusting were all measured rather than reasoned: the cycle contract's inversion (reverting the boundary to the contract the spec stated fails **five** listed node ids, zero collection errors, revert byte-compared), the queryset-polymorphism bullet's three exceptions (temp test, output quoted in row F17), and the `spec-051`-is-not-the-superseding-work negative (it is still `TODO` and its `permissions` references are to different modules). The eight-site, three-grammar flag on the cycle contract was the single most valuable thing this cohort produced for R2, and it held: sweeping the four spellings it named found sites in `## Goals`, `### Error shapes`, the Slice checklist, Decision 5 and three edge-case bullets that no single grep would have reached.

**Discharged in the spec by R2 — 18 findings.** The scope predicate (A2/B5), the GFK exclusion (A4/F13), the MTI parent-link exclusion and its deferred-extension paragraph (A5/F14), the hook gate in all five of its homes (A7/B7/B17/F16/F20), the unconditional `__isnull` disjunct (A8b), the seen-set-and-never-raise cycle contract across its eight sites (A10/A11/C3/C9/D1/F3/F4/F9), the sync-misuse probe shape and its named recourses (A15/B19/C8), the `filters/sets.py` precedent (A16/B20), the module-contents inventory (B2), the hook-return contract (B8/F15), Decision 6's zero-match citation and inverted premise (B12/L1), the unstated alias rejections and the raw `walker.py:212` (B14/F18), the two-of-twelve `### Error shapes` (C11/M2), the composite-FK skip (F12), the queryset-polymorphism bullet (F17/M3), `fields=[]`'s unstated second role (F21), the pre-archive path in Decision 1 and DoD item 1 (G1/L2 — the DoD command now exits 0), and all seven renamed/superseded Slice-1 test names. Decision 5's heading was renamed with them, since it asserted the inverted hook gate; the slug moved across 13 spec anchors and 4 rationale anchors with no foreign readers. R1a's request for a home for the sealed-boundary statement is met by a root-sealing paragraph in Decision 5 and the reworked step 4.

**Routed to the deferred-work catalog, not fixed — 3.** Finding **M1** (the `getattr(field, "is_relation", False)` fail-open shape) and **DRY D1** (the `_cascadable_edges` / `_cascadable_edge_names` existence challenge) are source-side maintainer calls, and this round writes no source. The out-of-territory note about the spec's card-id rot is frozen by the maintainer escalation in the build plan's `## R1 outcome`; every spelling survives byte-identical, verified. R1a's sequencing warning — that Decision 6's `TODO-BETA-046-0.1.1` sits inside the Consumer-recipe block R2 was asked to rewrite — was honoured: the block's reason was replaced around the id, and the id was not touched.

**Nothing from this cohort routes to R3**, as its headline result stated, and the R3 cycle's scope confirms it: R3 closes R1c's B4a alone.

Status set to `final-accepted`.

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
