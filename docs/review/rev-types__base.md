# Review: `django_strawberry_framework/types/base.py`

Status: verified

## DRY analysis

- None — `base.py` IS the single source for the `DjangoType` collection pipeline and for the Meta-vocabulary constants. The repeated-literal and near-copy candidates were all checked and are already either hoisted to a named module constant or are deliberately-distinct sibling messages (see `### DRY recap`). The module-scoped string-set / default constants (`RELATION_SHAPE_VALUES` / `DEFAULT_RELATION_SHAPE` at base.py:98-99, `STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY` at base.py:122-123, `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` at base.py:107-113, `_INTERFACES_SHAPE_ERROR_LEAD_IN` at base.py:818) are themselves the consolidation points the in-source comments document; folding them further would re-couple surfaces the comments explicitly keep apart.

## High:

None.

## Medium:

None.

## Low:

### `_validate_connection` carries a hard-coded `"0.0.9"` version literal in its error text

`_validate_connection` (base.py:206-211) rejects unknown `Meta.connection` sub-keys with `"Only 'total_count' is recognized in 0.0.9."`, and the docstring (base.py:185-186) also says "for ``0.0.9`` the only recognized sub-key". The package is now at `0.0.10` and the GLOSSARY (`docs/GLOSSARY.md:315`) similarly pins the connection-field paragraph to `0.0.9`. The literal is harmless today (the constraint itself is still accurate — `total_count` is still the only sub-key), but a version string baked into a consumer-visible error message drifts the moment a second sub-key ships. This is a stale-but-harmless comment/message, not a logic defect.

Defer until a second `Meta.connection` sub-key lands (the card that adds the second key already has to touch this `unknown`-guard and its message); at that point drop the version pin entirely rather than bumping it, so the message stops asserting a per-release vocabulary. No source edit this cycle.

### `_meta_optimizer_hints` error message exceeds the formatter target width

`_meta_optimizer_hints` (base.py:794-797) raises a single-line f-string error whose source line runs past 100 chars (graced under the 110 E501 ceiling per AGENTS.md #16, so ruff does not flag it). Every sibling validator in this file wraps its message across implicit-concatenated string lines; this one does not. Purely cosmetic — the formatter cannot break an f-string mid-token and the line is within the graced ceiling.

Defer until this message is next edited for content; wrap it across two implicitly-concatenated lines then to match the sibling validators. No standalone edit warranted.

## What looks solid

### DRY recap

- **Existing patterns reused.** The file routes every typo-guard through the shared `_format_unknown_fields_error` (base.py:801-815) — used by `_validate_optimizer_hints` (base.py:1174, 1184), `_selected_meta_targets` (base.py:1228), and `_select_fields` (base.py:1448, 1460) — so `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` / `nullable_overrides` / `relation_shapes` typos all surface in one consumer-visible shape. The unknown-vs-excluded target-guard prologue is single-sourced in `_selected_meta_targets` (base.py:1199-1239) and reused by both `_validate_nullability_override_targets` (base.py:1297) and `_validate_relation_shape_targets` (base.py:1369). The Relay-shape predicate is single-sited in `_is_relay_shaped` (base.py:446-457) and consumed at all four timings (`_validate_meta` connection/globalid/relation gates via base.py:1084, the H1 id-collision guard at base.py:570, and the pk-suppression branch at base.py:1558). The GlobalID validator (`_validate_globalid_strategy`, base.py:290-346) is the documented one-validator-two-sources point shared with `types/relay.py`. The `is_async_callable` sync-ness check (base.py:363) reuses `utils/typing.py` per the 0.0.9 DRY pass.
- **New helpers considered.** Considered folding the three Relay-Node gates (`_validate_connection`, `_validate_globalid_strategy`, `_validate_relation_shapes`) into one gate helper — rejected: the connection/globalid gates share the `_RELAY_NODE_GATE_INHERIT_TAIL` tail while the relation_shapes gate uses the spec-032-pinned "or remove the key." tail, and each runs a different shape-check body before the gate; the shared lead-in is already hoisted to `_RELAY_NODE_GATE_LEAD`, which is the correct granularity. Considered a shared `_normalize_*_spec` collapse — rejected: `_normalize_fields_spec` accepts the `"__all__"` sentinel that `_normalize_sequence_spec` must reject, distinct contracts.
- **Duplication risk in the current file.** The repeated `f"{model.__name__}.Meta..."` / `f"{meta.model.__name__}.Meta..."` message prefixes across the validators are intentional per-message human text, not a dispatch key — each names a distinct constraint and remediation; folding to a shared template would flatten the consumer-facing diagnostics. The `snake_case(name)` field-map key (base.py:488, 1388, 1572) is recomputed at each lookup rather than cached; on already-snake_case Django field names it is idempotent and the call is cheap, so the recompute is the simpler-readable factoring.

### Other positives

- **Two-stage Meta validation is principled.** Shape-only checks that need only the raw `Meta` (`_validate_meta`, base.py:995-1133) run at meta time; target-existence checks that need the selected fields + consumer-override union (`_validate_nullability_override_targets`, `_validate_relation_shape_targets`) run from `__init_subclass__` after `_select_fields`. The split is documented at each site and matches the spec-029 precedent.
- **`__init_subclass__` import-time discipline is correct.** The sentinel flip (`_is_default_get_queryset`) is stamped BEFORE the `meta is None` early-return (base.py:474-477) so abstract bases without `Meta` still propagate a custom `get_queryset` to concrete subclasses — pinned by the named test. The finalized-registry guard (base.py:479-483) fails loudly on post-finalize registration. `FilterSet` / `OrderSet` imports are deliberately function-local (base.py:142, 170) with explicit do-not-hoist comments to dodge the `types -> filters/orders -> types` module-load cycle.
- **Reflective access is all justified.** `cls.__dict__.get("Meta")` (own-class only, no MRO walk) is the deliberate counterpart to the MRO-walking `getattr` in `_validate_meta` (documented at base.py:1045-1052); `meta.__dict__` for the typo-guard is own-keys-only so base `Meta` keys are not re-flagged per subclass; `_detect_custom_get_queryset` walks `cls.__mro__` stopping at `DjangoType`. The `_id_annotation_is_relay_node_id` rewrite reads `cls.__annotations__["id"]` directly (no `typing.get_type_hints`) specifically to kill a 3.10-vs-3.11 interpreter-divergent branch — exactly the root-cause fix AGENTS.md #4 demands over a pragma.
- **Edge-case ordering is defensive.** `isinstance(shape, str)` runs before the `shape not in RELATION_SHAPE_VALUES` set membership (base.py:264) so an unhashable value raises `ConfigurationError` rather than leaking `TypeError: unhashable type` (spec-032 feedback P3). The `_RELAY_NON_INTERFACE_HELPERS` table matches by identity (`entry is helper`) because `relay.NodeID` is an `Annotated` alias, not a hashable class, and the named-helper rejection runs before the generic non-class branch so `relay.NodeID` gets a named message.
- **SyncMisuseError / async surface.** No `SyncMisuseError` raise or async resolver path lives in this module — the GlobalID-callable sync-ness gate (`_validate_globalid_callable`, base.py:349-374) promotes an `async def` encoder to a build-time `ConfigurationError` rather than letting a coroutine reach request time, which is the correct place to catch it.

### Summary

`types/base.py` is unchanged since baseline 14910230 (`git log 14910230..HEAD` empty, `git diff HEAD` empty) and does not appear in the spec-035 changed-file set (which touched `types/definition.py` + `types/resolvers.py`). It is the central, heavily-reviewed `DjangoType` collection engine: a 1635-line module of pure validation + annotation-synthesis logic with no schema-build, no ORM query, and no request-scope state. Every reflective access, every two-stage validation split, and every Meta-vocabulary constant is documented and single-sourced; the DRY consolidation points the module owns are at the correct granularity. No High or Medium findings. Two Lows, both stale-but-harmless message/width issues correctly deferred to the next edit that touches the message. No-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `270 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- No-source-edit cycle (shape #5). `base.py` is byte-identical to baseline 14910230 and to HEAD; this is a read-only review.
- Low #1 (`"0.0.9"` version literal in `_validate_connection` error text + docstring + GLOSSARY:315): forward-looking, deferred with trigger "until a second `Meta.connection` sub-key lands." The constraint is still factually correct (`total_count` is still the only sub-key), so no current defect — purely a future-drift risk. No edit this cycle.
- Low #2 (`_meta_optimizer_hints` message width): forward-looking, deferred to next content edit of that message. Within the graced 110-char E501 ceiling; ruff clean.
- No GLOSSARY-only fix in scope. GLOSSARY drift check (DjangoType, has_custom_get_queryset, globalid_strategy, relation_shapes, nullable_overrides, optimizer_hints) found prose consistent with the implementation; the `0.0.9` shipped-version pins are accurate, not stale.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No source edits, so no comment/docstring changes. The two Lows above are message-text observations deferred to their next content edit; neither warrants a standalone comment-only edit this cycle.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change occurred (read-only review of an unchanged file). Cited authority: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for this item.

---

## Verification (Worker 3)

### Logic verification outcome

No-source-edit cycle (shape #5). `git diff HEAD -- django_strawberry_framework/types/base.py` empty; `git diff --stat 14910230 -- django_strawberry_framework/types/base.py` empty; last-touch commit is `e30d77ab` ("Finish REVIEW of 0.0.9"), predating both the cycle baseline and HEAD. Zero this-cycle edits confirmed.

- **High / Medium:** none claimed, none found. Independent spot-checks of the `What looks solid` claims all hold against live source:
  - `__init_subclass__` import-time discipline + registration: function-local `FilterSet`/`OrderSet` imports at base.py:142 / base.py:170 carry explicit module-load-cycle comments (base.py:130 / base.py:156), dodging the `types -> filters/orders -> types` cycle. No import-time side effect beyond registration.
  - SyncMisuseError / async surface: grep confirms NO `SyncMisuseError` raise and NO `async def` resolver / `await` path in the module. The only async references are the build-time sync-ness gate `_validate_globalid_callable` (base.py:363, reusing `utils/typing.py::is_async_callable` imported at base.py:57) which promotes an `async def` encoder to a `ConfigurationError` rather than letting a coroutine reach request time — correct placement.
  - Meta handling / two-stage validation, reflective access, edge-case ordering: internally consistent and grep-confirmed at the cited symbols.
- **Low 1 (`"0.0.9"` literal in `_validate_connection` error + docstring, mirrored at GLOSSARY:315):** verdict — the literal documents the release the connection/`total_count` sub-feature SHIPPED (recognized-vocabulary as-of that release), NOT the current package `__version__`. Evidence: the `Meta.connection` opt-in `totalCount` entry sits under `## [0.0.9] - 2026-06-13` in CHANGELOG.md:31/37; package `__version__ = "0.0.10"` (django_strawberry_framework/__init__.py); the error text reads "Only 'total_count' is recognized in 0.0.9." (base.py:210) and the docstring "for ``0.0.9`` the only recognized sub-key" (base.py:184) — both are per-release vocabulary statements, and `total_count` IS still the only recognized sub-key (`set(connection) - {"total_count"}`, base.py:206). Factually accurate today; NOT a stale current-version reference. The defer (drop the version pin entirely when a 2nd sub-key ships) is correct. ACCEPTED no-action.
- **Low 2 (`_meta_optimizer_hints` >100-char error f-string, base.py:794-797):** confirmed single-line f-string within the graced 110-char E501 ceiling (AGENTS.md #16); ruff clean. Sibling validators wrap; this one cannot break mid-token. Cosmetic; deferred to next content edit. ACCEPTED no-action.

### DRY findings disposition

DRY None is sound: `base.py` IS the single source for the `DjangoType` collection pipeline and Meta-vocabulary constants. Spot-confirmed the consolidation points are real and at the right granularity — the three Relay-Node gates legitimately differ in their gate tail (`_RELAY_NODE_GATE_INHERIT_TAIL` vs the spec-032 "or remove the key." tail) and shape-check body, and the shared lead-in is already hoisted to `_RELAY_NODE_GATE_LEAD`. No carry-forward.

### Temp test verification

- None used. No-source-edit cycle; behavior is unchanged from a fully-reviewed baseline, so no focused-test confirmation required (worker-3.md: do not run pytest preemptively).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/base.py` checklist box.

Shape #5 terminal-verify checklist all met: (a) per-item `git diff HEAD` empty + absent from the base.py diff stat; (b) every Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.`; (c) both Lows carry verbatim in-source trigger phrasing, no GLOSSARY-only fix in scope; (d) changelog `Not warranted` cites BOTH AGENTS.md #21 AND active-plan silence, `git diff HEAD -- CHANGELOG.md` empty; (e) `uv run ruff format --check` ("1 file already formatted") + `uv run ruff check` ("All checks passed!") on base.py.

---

## Iteration log

(none)
