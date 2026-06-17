# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## DRY analysis

- **`_will_lazy_load_single` (resolvers.py:136) and `_fk_attname_is_deferred` (resolvers.py:89) share the `<name> in getattr(root, "__dict__", {})` loaded-signal probe, but with deliberately divergent tails.** `_will_lazy_load_single` falls back to `_state.fields_cache` membership (relation-instance cache); `_fk_attname_is_deferred` falls back to `get_deferred_fields()` membership (column-deferral cache). These are two different Django caches answering two different questions ("is the related object loaded?" vs "is the FK column loaded?"). Defer with explicit trigger: **"Defer until a third caller needs the bare `__dict__` loaded-signal; only then extract `def _attr_in_instance_dict(root, name) -> bool` for the first line of both."** Folding only the shared first line at N=2 is net-negative — the bodies diverge immediately after and the one-liner reads clearer inline than as a named helper indirection.

## High:

None.

## Medium:

None.

## Low:

### Archived design specs still cite the removed `_is_fk_id_elided` helper

Commit `79b74b46` deleted `resolvers.py::_is_fk_id_elided` (inlined into `forward_resolver` via the threaded `elisions` read at resolvers.py:370-380). Two archived design docs still reference the symbol by `path::_is_fk_id_elided`:

- `docs/SPECS/spec-015-relay_interfaces-0_0_5.md:357`
- `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:258,336,383,386`

These are completed/archived design docs under `docs/SPECS/` — historical snapshots of the design at their authoring time, not standing references that must track source renames. AGENTS.md #27's grep-sweep-on-rename rule targets live code comments and standing docs; archived specs are deliberately frozen records. So this is a non-defect-today **forward-Low**, not an action-now stale-doc. Defer with trigger: **"Defer unless a future reader treats `docs/SPECS/spec-003`/`spec-015` as a live source map; if so, add a one-line 'superseded by inlined `forward_resolver` elisions read (0.0.10)' note rather than rewriting the frozen design text."** Do NOT rewrite archived spec bodies as part of this cycle — they are intentionally immutable history.

## What looks solid

### DRY recap

- **Existing patterns reused.** The resolve-time elision guard reuses the optimizer subpackage's canonical sentinels (`DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_STRICTNESS` from `optimizer/_context.py`) and the canonical key builders (`resolver_key`, `runtime_path_from_info` from `optimizer/plans.py`); the N+1 logger is aliased (not re-created) from `optimizer.logger` (resolvers.py:38). `FieldMeta` shape construction goes through the canonical `FieldMeta.from_django_field` / `_from_field_shape` (resolvers.py:291-292) so the resolver's relation-kind classification cannot drift from the walker's. Cardinality dispatch reuses `is_many_side_relation_kind` and `instance_accessor` from `utils/relations` (resolvers.py:50). The L3 feedback refactor (`planned`/`precomputed_key`/`_PLAN_UNREAD` threading, resolvers.py:60,224-232) is itself a DRY win — it collapses a duplicated `info.path` walk between the elision check and the N+1 check into one per row.
- **New helpers considered.** `_fk_attname_is_deferred` (resolvers.py:75) was extracted from `_build_fk_id_stub` as a named single-source loaded-signal for the FK *column* — correct extraction, mirrors `_will_lazy_load_single` for the relation *instance*. The shared `__dict__` first-line fold was evaluated and rejected at N=2 (see DRY analysis).
- **Duplication risk in the current file.** The 2× `__dict__` literal (resolvers.py:89,136) and the two near-twin loaded-check helpers are intentional sibling design over two distinct Django caches (column-deferral vs relation-instance), not a copy. The three cardinality-branch resolver closures (`many_resolver`, `reverse_one_to_one_resolver`, `forward_resolver`) share the `_check_n1(...)` preamble call but have genuinely distinct bodies (prefetch-cache fast path / DoesNotExist swallow / FK-id-elision + force-unplanned) — folding would re-couple divergent logic.

### Other positives

- **The FK-id-elision resolve-time safety guard (the data-correctness crux) is correct and load-bearing.** Traced the full invariant: `walker.py::_record_relation_access` (walker.py:500, appends `resolver_identities` into `planned_resolver_keys` at walker.py:613) runs BEFORE the elision append at walker.py:514, so every key in `fk_id_elisions` is also in `planned`. That is exactly what makes `force_unplanned` necessary: an elided-but-deferred FK key WOULD short-circuit `_check_n1` on the planned membership (resolvers.py:233) and stay silent. The guard chain — `_fk_attname_is_deferred` → `_build_fk_id_stub` returns `_FK_ELISION_UNSAFE` → `forward_resolver` sets `elision_unsafe=True` → `_check_n1(force_unplanned=True)` bypasses the planned short-circuit and re-probes the lazy-load — prevents serving a stub built from a column that would lazy-load, and makes the fallback strictness-visible instead of a silent per-row query. No wrong/stale/leaked data path found.
- **Deferred-column detection is robust against test doubles AND real instances.** `_fk_attname_is_deferred` confirms deferral only when the column is absent from `__dict__` AND `root` exposes a real `get_deferred_fields()` listing it (resolvers.py:89-94). A plain double (no `get_deferred_fields`) is treated as loaded — matching the module-wide "test-double = loaded" contract. Pinned by both a double-based test (`test_fk_id_stub_returns_unsafe_sentinel_when_attname_deferred`) and a real `Item.objects.only("name")` Django test (`test_fk_id_elision_falls_back_on_real_deferred_only_instance`, django_db).
- **No false-fallback on the loaded path.** On the elided path the optimizer does not also `select_related` the relation, so `fields_cache` does not hold the related object; a deferred FK therefore correctly forces the probe. A fully-loaded FK column (the optimizer-owned-projection norm and the consumer-`.only()`-that-includes-the-FK case) builds the stub as before — `test_fk_id_stub_returns_unsafe_sentinel_when_attname_deferred` pins the loaded-double still returns a stub (pk=42).
- **Many-side prefetch fast path (feedback H1) is correct.** `many_resolver` (resolvers.py:341-347) reads `_prefetched_objects_cache[accessor_name]._result_cache` directly and returns it, skipping the `manager.all()` clone + `list()` copy; same rows, same order; any miss falls through to `list(getattr(root, accessor_name).all())`. The N+1 probe and the fast-path read use the same `accessor_name` key, so they cannot disagree. Many-side cache check deliberately does NOT apply the `__dict__` short-circuit (resolvers.py:143-155) — documented as preventing a consumer-assigned attribute from silently exempting the many-side strictness path; pinned by `test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy`.
- **Accessor/field-name split is consistent.** `field_name` keys the PLAN lookup (walker vocabulary); `accessor_name` keys the instance CACHE probes (Django prefetch/fields caches store under the accessor, which diverges for reverse relations without `related_name`). The split is threaded uniformly through `_check_n1` and all three closures; pinned by `test_check_n1_probes_prefetch_cache_under_accessor_name`.
- **`router.db_for_read` stub hydration is correct multi-DB behavior.** `_build_fk_id_stub` (resolvers.py:116-122) sets `state.adding=False` and `state.db` via `router.db_for_read(related_model, instance=root if root has _state else None)` — forwards the parent row as the routing hint when present. Three dedicated tests pin the router contract (instance forwarded / None when parent lacks `_state` / no router call on null FK). GLOSSARY:887 documents exactly this.
- **No import-time side effects.** Module top level is imports + three module-constant sentinels (`_EMPTY_ELISIONS`, `_PLAN_UNREAD`, `_FK_ELISION_UNSAFE`) + function defs. No ORM query, no schema build, no registry mutation at import. The `_EMPTY_ELISIONS` frozenset sentinel avoids a fresh empty-set allocation per forward resolve. Import direction is one-way (resolvers imports from optimizer/utils/registry/exceptions; the module docstring's stated invariant "resolvers.py imports nothing from base.py" holds — confirmed in the import list).
- **Common-request fast path preserved.** `forward_resolver` reads both sentinels and short-circuits to a bare `getattr(root, field_name)` when neither elisions nor planned is active (resolvers.py:376-377), skipping the `info.path` walk entirely for the un-optimized common shape. `elisions` is only read when `field_meta.attname is not None` (resolvers.py:370-374), avoiding the context read for relations that can't be FK-id-elided.
- **GLOSSARY consistency.** GLOSSARY "FK-id elision" (GLOSSARY:550-567) documents the 0.0.10 consumer-`.only()` loaded-check ("falls back loudly (strictness-visible) when a consumer projection deferred it, rather than a silent per-row lazy load", GLOSSARY:565) — an exact match for this file's Decision 5 implementation. No drift on any resolver-related symbol.
- **Test discipline.** spec-035 Decision 5 is pinned at three layers: a direct unit on `_build_fk_id_stub` (sentinel + loaded-double), a double-based resolver-level fallback test parameterized over QUERY/mutation arms asserting OptimizerError under "raise" and warn+normal-resolve under "warn", and a real django_db `.only()` test. The deferred FK column is guarded by an `AssertionError`-raising property in the doubles so any silent read fails the test.

### Summary

No-source-edit cycle (shape #5). This-cycle diff vs HEAD is empty; the spec-035 Decision 5 hardening (`_FK_ELISION_UNSAFE` sentinel, `_fk_attname_is_deferred`, `force_unplanned`) and the prior L3 threading refactor are already in HEAD (commits `8866fcea`, `79b74b46`). The FK-id-elision resolve-time safety guard — the data-correctness crux flagged in the dispatch — is correct: I traced the walker invariant (every elided key is also a planned key, recorded by `_record_relation_access` before the elision append) and confirmed `force_unplanned` exists precisely to defeat the planned short-circuit so a deferred-FK fallback stays strictness-visible and never serves a stub built from a column that would lazy-load. Deferred-column detection is robust against both test doubles and real `.only()` instances, the many-side prefetch fast path is correct, no import-time side effects, GLOSSARY is consistent. No High, no Medium. One forward-Low (archived design specs cite the removed `_is_fk_id_elided` symbol — frozen historical record, do not rewrite). One deferred DRY opportunity (shared `__dict__` loaded-signal first line, fold only at N=3). No source edit warranted.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged.
- `uv run ruff check .` — pass; "All checks passed!" (one pre-existing COM812/formatter-conflict warning, unrelated to this file).

### Notes for Worker 3
- Shape #5: zero edits to any tracked file (source, tests, GLOSSARY, CHANGELOG).
- Low #1 (archived-spec `_is_fk_id_elided` references): forward-Low, intentionally NOT fixed — `docs/SPECS/spec-003` and `spec-015` are frozen historical design records, not standing references; AGENTS.md #27 rename-sweep targets live code/standing docs only. Trigger quoted in the Low body.
- DRY analysis item (shared `__dict__` loaded-signal): deferred with trigger "third caller needs the bare `__dict__` loaded-signal"; no action this cycle.
- No GLOSSARY-only fix in scope — GLOSSARY:550-567 already matches the implementation exactly.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted: the spec-035 Decision 5 rationale is documented inline at the sentinel definition (resolvers.py:62-72), `_fk_attname_is_deferred` (resolvers.py:76-88), `_build_fk_id_stub` (resolvers.py:98-108), the `force_unplanned` parameter doc (resolvers.py:210-217), and the `forward_resolver` fallback comments (resolvers.py:381-393) — all accurate against the implementation and cross-referenced to the design decision and feedback items.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no source/test edit this cycle; AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_10.md`, silent on changelog edits) both apply.

---

## Verification (Worker 3)

### Logic verification outcome

Re-derived the FK-elision guard correctness independently against live HEAD source (`8866fcea`/`79b74b46` already in HEAD `58ca2def`); did not trust the artifact prose.

- **Walker invariant (every elided key is also planned).** `optimizer/walker.py::_plan_select_relation` calls `_record_relation_access` (walker.py:500-506) BEFORE the elision append; `_record_relation_access` appends `resolver_identities` into `plan.planned_resolver_keys` (walker.py:613). The SAME `resolver_identities` is then appended into `plan.fk_id_elisions` (walker.py:514). So `fk_id_elisions ⊆ planned_resolver_keys` — confirmed by reading source ordering, not the artifact. This is exactly why `force_unplanned` must exist.
- **Invariant 1 (no stub from a deferred column).** `_build_fk_id_stub` (resolvers.py:97) returns `_FK_ELISION_UNSAFE` at line 112 (the `_fk_attname_is_deferred` branch) BEFORE the `getattr(root, field_meta.attname)` read at line 113. The deferred column is never read on the unsafe path. `forward_resolver` treats the sentinel as not-elided (resolvers.py:387-393) and falls through. Confirmed no wrong/stale/leaked FK-id path.
- **Invariant 2 (force_unplanned bypasses the planned short-circuit).** resolvers.py:233 `if key in planned and not force_unplanned: return` — when `force_unplanned=True`, `not force_unplanned` is False, so the early return is skipped regardless of `key in planned`, and the lazy-load probe (resolvers.py:240-244) runs. `forward_resolver` threads `force_unplanned=elision_unsafe` (resolvers.py:403). Proven in isolation by temp test (see below): WITHOUT the flag a planned+lazy key is silently swallowed; WITH it the same key raises.
- **Invariant 3 (deferred-vs-loaded detection robust).** `_fk_attname_is_deferred` (resolvers.py:89-94): absent from `__dict__` AND a real `get_deferred_fields()` listing the column. A loaded double (column in `__dict__`) → not deferred; a plain double with no `get_deferred_fields` → treated loaded (module-wide test-double=loaded contract). Temp test exercises all three shapes.
- **Invariant 4 (no permission bypass from the L3 refactor).** resolvers.py contains NO permission / get_queryset / async / await / visibility code (grep = zero hits). The relation resolvers do plain `getattr`/manager reads over already-fetched data; get_queryset visibility + `check_*_permission` composition lives in `permissions.py`, `connection.py`, `relay.py`, `filters/`, `types/relay.py` — not in this target file. The L3 elision/threading refactor is structurally incapable of bypassing permissions because it never queries or filters; invariant #4's risk surface is not in this artifact. No bypass introduced.

All High / Medium: none claimed, none found. The one Low is correctly-not-fixed (below).

### DRY findings disposition

Shared `getattr(root, "__dict__", {})` first-line probe appears at exactly N=2 (resolvers.py:89, :136) — confirmed by grep. Bodies diverge immediately (`get_deferred_fields()` membership vs `_state.fields_cache` membership — two distinct Django caches). Defer-until-N=3 trigger is grep-accurate and sound; folding at N=2 is net-negative. Carried forward, no action.

### Temp test verification

- Temp test: `docs/review/temp-tests/types/test_w3_fk_elision_guard.py` (gitignored) — 9 tests, independent re-derivation, distinct framing from the permanent suite. `uv run pytest ... --no-cov` → **9 passed**.
  - `test_check_n1_planned_key_silenced_WITHOUT_force_unplanned` (no raise) + `test_check_n1_force_unplanned_bypasses_short_circuit_and_raises` (raises) jointly prove Invariant 2 IN ISOLATION — the bug exists without the flag, the flag fixes it.
  - `test_check_n1_force_unplanned_stays_silent_when_actually_loaded` and `test_resolver_loaded_fk_with_planned_key_does_not_spuriously_raise` are negative controls — the guard does not over-fire on a genuinely-loaded FK.
  - `test_resolver_real_deferred_only_raises_via_full_closure` (django_db) drives a real `Item.objects.only("name")` instance through the full `forward_resolver` closure to a loud `OptimizerError`.
- Disposition: deleted at cycle closeout (Worker 0). The behavior is already pinned by the permanent suite (`tests/types/test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk` parameterized + `test_fk_id_elision_falls_back_on_real_deferred_only_instance` django_db + `test_fk_id_stub_returns_unsafe_sentinel_when_attname_deferred`), so no promotion needed — the temp test was confirmation, not the sole proof.

### Low / shape-#5 / changelog disposition

- **Low (archived-spec `_is_fk_id_elided` refs):** correctly-not-fixed. `grep -rn "_is_fk_id_elided" django_strawberry_framework/` → zero (symbol fully removed from source). Surviving only in `docs/SPECS/spec-003-...` and `docs/SPECS/spec-015-...` (latter `Status: final`) — frozen archived specs; AGENTS.md #27 rename-sweep targets live code/standing docs, not frozen history. Forward-Low with verbatim trigger is the correct disposition. Do NOT rewrite.
- **Shape #5:** (a) `git diff HEAD -- types/resolvers.py` empty; target absent from owned-path diff stat. (b) All three Worker 2 sections open `Filled by Worker 1 per no-source-edit cycle pattern.` (c) The one Low carries verbatim in-source trigger phrasing; no GLOSSARY-only fix. (d) Changelog `Not warranted` cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND active-plan silence; `git diff HEAD -- CHANGELOG.md` empty; internal-only framing matches (no public-API surface changed). (e) `uv run ruff format --check` → "1 file already formatted"; `uv run ruff check` → "All checks passed!" (the COM812 warning is the documented pre-existing formatter-conflict noise, file-independent).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/resolvers.py` checklist box in `docs/review/review-0_0_10.md`.
