# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## DRY analysis

- **`resolver_key(parent_type, field_name, runtime_path_from_info(info))` 3-tuple build is duplicated across two sites in this file — defer with trigger.** Both `_is_fk_id_elided` (`types/resolvers.py:70`) and `_check_n1` (`types/resolvers.py:170`) construct the identical `resolver_key(parent_type, field_name, runtime_path_from_info(info))` key from the same closure-captured triple, then test membership one line below (`key in elisions` / `key in planned`). A thin `_resolver_key_from_info(parent_type, field_name, info)` helper would collapse the build. Today only two sites exist and the helper would obscure the `key in <set>` near-symmetry that reads clearly inline. **Defer until a third site in this file needs the same key-from-info build** (most plausibly a per-field strictness-override hook or an O5-shape planned-writes mutation seam). This is the same trigger the prior (now-superseded) artifact recorded; it has not fired.
- **Cross-folder `_field_meta_for_resolver` test-double fallback already delegates to the shared shape helper — no act-now opportunity, owned by the folder pass.** `_field_meta_for_resolver` (`types/resolvers.py:206-230`) no longer line-duplicates `FieldMeta.from_django_field`; its non-`is_relation` test-double branch now calls `FieldMeta._from_field_shape(field, is_relation=True)` (`types/resolvers.py:229`), the shared helper extracted into `optimizer/field_meta.py::FieldMeta._from_field_shape` (`optimizer/field_meta.py:163`). The earlier cross-folder duplication DRY candidate is therefore already consolidated upstream. Recap-only here; any residual cross-folder shaping question belongs to `rev-types.md` (folder pass), not this per-file scope.

## High:

None.

## Medium:

None.

## Low:

### `_check_n1` with `kind="connection_to_attr"` and `to_attr=None` would raise `TypeError` from `getattr(root, None, None)`

At `types/resolvers.py:176`, the connection branch evaluates `lazy = getattr(root, to_attr, None) is None`. The default for the keyword-only `to_attr` parameter is `None` (`types/resolvers.py:131`). If a caller passes `kind="connection_to_attr"` without `to_attr`, this becomes `getattr(root, None, None)`, which raises `TypeError: attribute name must be string`. This is NOT a production defect: the sole `connection_to_attr` caller (`connection.py::_resolve` at `connection.py:1148-1156`) always supplies `to_attr=_relation_connection_to_attr(relation_field_name)` (a non-empty `str`), and the docstring (`types/resolvers.py:154-164`) scopes the `connection_to_attr` value to the synthesized connection resolver only — the documented `kind=None` test-double escape hatch routes to the single-valued cache check, never the `connection_to_attr` branch. Recorded-intent Low: the parameter pairing is a documented contract (`connection_to_attr` implies a supplied `to_attr`), the blast radius is a single internal call site, and a malformed test-double call failing loudly with `TypeError` is acceptable. No fix warranted; flagged only so a future caller adding a second `connection_to_attr` site supplies `to_attr` and so the docstring's "connection contract" pairing is visible as load-bearing.

### Docstring build-phase version anchors (`B2`/`B3`/`Round-4 S3`/spec decision IDs) are provenance, not consumer contract

The module is dense with internal build-phase tags: `B2` (`types/resolvers.py:58`, `74`, `290`), `B3` (`types/resolvers.py:134`, `254`), `Round-4 review S3` (`types/resolvers.py:151`, `264`), and several `spec-011`/`spec-033 Decision N` references. These are accurate historical provenance and do not rot the way a version-pinned ships-THIS-release promise does (per my recurring calibration, version-pinned labels are Low unless co-occurring with a now-false forward-reserved-API promise — none here). No drift detected; recorded only to confirm the version-anchor scan was performed and cleared. No fix warranted.

## What looks solid

### DRY recap

- **Existing patterns reused.** Many-side classification routes through the single shared classifier `is_many_side_relation_kind` from `utils/relations.py:80` at both decision points — `field_meta.is_many_side` (which delegates to `is_many_side_relation_kind(self.relation_kind)`, `optimizer/field_meta.py:134-136`) selects the resolver shape in `_make_relation_resolver` (`types/resolvers.py:269`), and `_check_n1` re-derives the cache-probe shape from `is_many_side_relation_kind(kind)` on the same `field_meta.relation_kind` value (`types/resolvers.py:179`). The two dispatch paths are consistent by construction — same classifier, same `kind` — so a resolver built as many-side can never probe the single-valued cache. Accessor-vs-field-name vocabulary is centralized in `instance_accessor` (`utils/relations.py:85`). Context reads go through the shared `get_context_value` (`optimizer/_context.py:45`) which swallows `TypeError`/`KeyError`/`AttributeError` and returns the default, so all three context lookups (`_is_fk_id_elided`, `_check_n1`'s `planned`/`strictness`) are frozen-context-safe without local guards.
- **New helpers considered.** `_resolver_key_from_info` two-site collapse — rejected for now (deferred with trigger, see DRY analysis). `_name_resolver` already centralizes the three cardinality-branch `__name__` stamps.
- **Duplication risk in the current file.** The three nested resolver closures (`many_resolver`, `reverse_one_to_one_resolver`, `forward_resolver`, `types/resolvers.py:271-293`) share the `_check_n1(...)` preamble but diverge in body (list-materialize / try-except DoesNotExist / FK-id-elision-then-getattr). These are intentional sibling shapes, not duplication — collapsing them would require per-branch flags that obscure the cardinality contract. The shadow overview reports zero repeated string literals, confirming no string-keyed-dispatch DRY signal.

### Other positives

- **The OptimizerError raise site is correct and tightly scoped.** `_check_n1` (`types/resolvers.py:166-190`) gates the raise behind four sequential conditions — `planned is not None` (optimizer actually ran), `key not in planned` (this relation was not planned), the cache/`to_attr` probe shows a real lazy load (`lazy`), and `strictness == "raise"`. Each gate has a dedicated test in `tests/types/test_resolvers.py` (`test_check_n1_planned_absent_is_silent`, `test_check_n1_planned_hit_is_silent`, `test_check_n1_returns_when_relation_is_already_loaded`, `test_check_n1_default_strictness_off_is_silent_on_lazy_load`, `test_check_n1_raise_strictness_raises_on_lazy_load`). The raise type `OptimizerError` (`exceptions.py:33`, subclass of `DjangoStrawberryFrameworkError`) matches the live GLOSSARY contract at `docs/GLOSSARY.md:1260` and the same-machinery connection claim at `docs/GLOSSARY.md:1264`.
- **The connection hand-off is parameterized through the SAME checker, not a second one.** `connection.py::_resolve` (`connection.py:1148-1156`) calls `_check_n1` with `kind="connection_to_attr"`, the windowed `to_attr` (`_dst_<field>_connection`), the declaring type as `parent_type`, and `relation_field_name` (NOT the generated connection name) — exactly the vocabulary the walker keyed planned connections under (`connection.py:1099-1103`). The `to_attr` probe (`getattr(root, to_attr, None) is None`, `types/resolvers.py:176`) correctly treats a present windowed page as "already served, silent" and an absent one as "will query per-parent" — matching the prefetched-page semantics. The `reason` suffix (`types/resolvers.py:186`) is appended only when supplied, so list-relation calls (no `reason`) produce the byte-identical pre-slice message while connection fallbacks read as actionable. Live coverage: `tests/test_relay_connection.py:2054`/`2071` pin the exact `reason` strings.
- **Prefetch-cache contract is precise and asymmetric by design.** `_will_lazy_load_single` (`types/resolvers.py:90-105`) treats both `root.__dict__` and `root._state.fields_cache` as cached (covering Django descriptor population and assigned-instance paths plus synthetic test doubles), while `_will_lazy_load_many` (`types/resolvers.py:108-120`) deliberately consults ONLY `_prefetched_objects_cache` and does NOT apply the `__dict__` short-circuit — the docstring explains this prevents a consumer-assigned `root.<field>` attribute from silently exempting the many side from the N+1 contract. `test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy` pins it.
- **Accessor-vs-field-name divergence handled correctly.** `_check_n1` keys the PLAN lookup on `field_name` (walker vocabulary) but keys the instance CACHE probe on `accessor_name` (Django stores prefetch/fields caches under the accessor, which diverges for reverse relations without `related_name`). `test_check_n1_probes_prefetch_cache_under_accessor_name` pins the divergence with a `plainbook` reverse relation.
- **FK-id elision path is read-only and DB-router-aware.** `_build_fk_id_stub` (`types/resolvers.py:74-87`) builds a `pk`-only target stub from `root.<attname>`, stamps `_state.adding = False` and `_state.db = router.db_for_read(...)` (with the source instance as routing hint when it has `_state`) so the stub is multi-DB-correct and is not mistaken for an unsaved instance. Returns `None` cleanly when `attname`/`related_model` is missing or the FK id is unset. Relay GlobalID handling is explicitly kept out of this path (`types/resolvers.py:60-63`), avoiding overlap with `types/relay.py`.
- **Sync-only posture is honest and fail-loud.** The synthesized connection resolver is sync-pipeline-only with no `resolver=` async seam; an async-`get_queryset` Relay target raises `SyncMisuseError` inherited from the pipeline (`connection.py:1105-1111`), not silently mishandled. The list-relation resolvers are likewise sync (`list(getattr(root, accessor_name).all())` is prefetch-aware on or off the optimizer) — consistent with the package's intentional sync/async-twin posture.
- **Import layering is clean and one-way.** `resolvers.py` imports from `optimizer/` (`logger`, `_context`, `field_meta`, `plans`), `registry`, `utils/relations`, and `exceptions` — and imports NOTHING from `types/base.py` (module docstring `types/resolvers.py:16-21` documents this deliberately so `DjangoType.__init_subclass__` can import `_attach_relation_resolvers` without a circular back-reference). `connection.py` imports `_check_n1` from here (`connection.py:69`), confirming this module is a leaf that the connection field depends on, not vice versa.

### Summary

`resolvers.py` attaches cardinality-aware relation resolvers at `DjangoType` finalization time and centralizes the optimizer's prefetch-cache and N+1-strictness contract. The 0.0.9 focus areas — the `OptimizerError` raise site and the connection hand-off — are correct, tightly gated, and well-tested: the raise fires only behind four sequential gates (optimizer-ran, not-planned, actually-lazy, strictness=raise), and the connection path reuses the SAME `_check_n1` checker via a `kind="connection_to_attr"` + `to_attr` parameterization rather than a second checker, keyed under the walker's own resolver-key vocabulary for "planned -> silent" parity. The stale on-disk artifact's lone Medium (GLOSSARY `RuntimeError` vs `OptimizerError` drift) is ALREADY FIXED in live source (`docs/GLOSSARY.md:1260` now reads `OptimizerError`) and was deliberately NOT re-raised. No High or Medium findings; two recorded-intent Lows (a documented `to_attr=None` contract pairing that fails loudly only on a non-existent malformed test-double call; cleared version-anchor scan). No source edit warranted — this qualifies as a no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `265 files left unchanged` (no source change).
- `uv run ruff check --fix .` — pass; `All checks passed!` (no source change).

### Notes for Worker 3
- **Low #1 (`to_attr=None` + `connection_to_attr` -> TypeError):** recorded-intent, no fix. Production sole caller `connection.py:1148-1156` always supplies a `str` `to_attr`; docstring (`types/resolvers.py:154-164`) scopes the value to the connection resolver and the `kind=None` test-double escape routes to the single-valued check. Failing loudly with `TypeError` on a malformed test-double call is acceptable per AGENTS.md root-cause posture (no defensive try/except band-aid warranted).
- **Low #2 (build-phase version anchors):** recorded-intent, no fix; provenance tags are accurate, no rot, no forward-API promise.
- **Stale-artifact Medium NOT re-raised:** prior artifact's GLOSSARY `RuntimeError`->`OptimizerError` drift is already fixed in live source (`docs/GLOSSARY.md:1260`, `1264`).
- No GLOSSARY-only fix in scope.

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, GLOSSARY, or behavior change in this cycle. Per AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan's silence on a changelog entry for this item.

---

## Verification (Worker 3)

Shape #5 no-source-edit, terminal verify. Baseline SHA `0872a20fcbecf870b3669742f108364202709e26`.

### Logic verification outcome

**No High / Medium findings** — confirmed. Two Lows, both recorded-intent / forward-looking, verified:

- **Low #1 (`to_attr=None` + `kind="connection_to_attr"` → TypeError):** driven LIVE — `_check_n1(..., kind="connection_to_attr", to_attr=None)` raises `TypeError: attribute name must be string, not 'NoneType'` from `getattr(root, None, None)` (`types/resolvers.py #"getattr(root, to_attr, None)"`). NOT a production defect: the sole `connection_to_attr` caller `connection.py::DjangoConnectionField._resolve` always supplies a non-empty `str` `to_attr=_relation_connection_to_attr(relation_field_name)` (read at `connection.py` `_check_n1(...)` call, `kind="connection_to_attr", to_attr=to_attr`). Documented contract pairing, single internal call site, fails loud on a malformed test-double — correctly no-fix.
- **Low #2 (build-phase `B2`/`B3`/`Round-4 S3`/spec version anchors):** accurate historical provenance, no rot, no co-occurring forward-reserved-API promise — confirmed by reading the cited docstring lines. Correctly no-fix.

**OptimizerError four-gate raise — driven LIVE** (`docs/review/temp-tests/types_resolvers/probe.py`, `config.settings`): each of the four gates independently silences — (1) `planned is None` returns even with `strictness="raise"`; (2) `key in planned` returns; (3) not-lazy (single `__dict__` populated) returns; (4) `strictness="off"` returns on a genuinely-lazy load. Only all-four-met raises `OptimizerError("Unplanned N+1: books")` (confirmed `isinstance` of `DjangoStrawberryFrameworkError`). Each gate is test-pinned (`test_check_n1_planned_absent_is_silent`, `_planned_hit_is_silent`, `_returns_when_relation_is_already_loaded`, `_default_strictness_off_is_silent_on_lazy_load`, `_raise_strictness_raises_on_lazy_load` — all grep-match `tests/types/test_resolvers.py`).

**Prefetch-cache asymmetry — driven LIVE:** `_will_lazy_load_single` honors the `root.__dict__` short-circuit (consumer-set attr → not lazy); `_will_lazy_load_many` deliberately does NOT (consumer-set `__dict__["books"]` STILL lazy; only `_prefetched_objects_cache` exempts). This is the documented asymmetry that prevents a consumer-assigned attribute from silently bypassing the many-side N+1 contract (`test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy` pins it). Single-valued path covers both `__dict__` and `_state.fields_cache`.

**Connection hand-off — same checker, walker vocabulary, driven LIVE:** `connection.py::_resolve` calls `_check_n1` with `relation_field_name` (str, NOT the generated connection name), `declaring_type`, `kind="connection_to_attr"`, and `to_attr=_relation_connection_to_attr(relation_field_name)`. The walker keys planned connections under the SAME `resolver_key(type_cls, relation_field_name, runtime_path)` vocabulary (`optimizer/walker.py` `_plan_connection_relation` passes `relation_field_name`, not the `_dst_*_connection` accessor) → "planned → silent" parity through ONE checker, not a second. Probed: `to_attr` present → silent; absent → raises with `reason` suffix appended (`Unplanned N+1: books (not window-planned; resolving per-parent)`). Reason pins `tests/test_relay_connection.py:2054`/`2071` grep-match.

**Cross-cutting confirmations:** many-side dispatch routes through the shared `is_many_side_relation_kind` (`utils/relations.py`) at both the resolver-shape selection and the cache-probe, so the two can't diverge. `_field_meta_for_resolver` test-double branch delegates to the shared `FieldMeta._from_field_shape(is_relation=True)`. Import layering is a clean one-way leaf: `resolvers.py` imports nothing from `types/base.py` (only the docstring mentions it); `base.py` imports `_attach_relation_resolvers` from here. All three context reads go through `get_context_value` (`optimizer/_context.py`), which swallows `TypeError`/`KeyError`/`AttributeError` → frozen-context-safe. Sync-only posture is honest (async `get_queryset` → inherited `SyncMisuseError`, fail-loud). GLOSSARY `docs/GLOSSARY.md:1260`/`1264` read `OptimizerError` — the stale on-disk artifact's `RuntimeError` Medium is already fixed in live source and correctly NOT re-raised.

### DRY findings disposition

Both DRY items carry forward correctly: (1) `_resolver_key_from_info` two-site collapse deferred-with-trigger (third in-file key-from-info site) — same trigger the prior superseded artifact recorded, unfired; (2) the cross-folder `_field_meta_for_resolver` shape helper is ALREADY consolidated upstream into `FieldMeta._from_field_shape` (confirmed at `types/resolvers.py #"FieldMeta._from_field_shape(field, is_relation=True)"`) — recap-only, owned by the folder pass.

### Temp test verification

- `docs/review/temp-tests/types_resolvers/probe.py` — drove the four-gate raise, the single-vs-many prefetch-cache asymmetry, the `connection_to_attr` present/absent/None trio (Low #1's TypeError), and `OptimizerError`-is-`DjangoStrawberryFrameworkError`. All assertions held.
- Disposition: deleted at cycle closeout by Worker 0; behavior is already covered by the permanent pins above (no promotion needed).
- Focused run: `uv run pytest tests/types/test_resolvers.py -o addopts="" -k "check_n1 or relation_resolver or fk_id or will_lazy or field_meta_for"` → **24 passed**.

### Shape #5 checks

1. `git diff --stat 0872a20… -- django_strawberry_framework/types/resolvers.py` is **empty** (byte-unchanged). Wider stat is dirty only at closed verified+`[x]` sibling cycles (conf/connection/exceptions/filters.factories/filters.sets/list_field/inspect/optimizer.extension/selections/walker/orders.factories/orders.inputs + GLOSSARY + 3 tests); `feedback2/3.md` delete = AGENTS.md #33. The cycle's "Files touched: None" claim holds.
2. Each Worker 2 section starts with `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed.
3. Both Lows are recorded-intent with explicit no-fix rationale; no GLOSSARY-only fix in scope — confirmed.
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty — confirmed. Internal-only framing honest (zero source/test/GLOSSARY/behavior change this cycle).
5. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (All checks passed) — pass (COM812 standing notice only).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/resolvers.py` checklist box.
