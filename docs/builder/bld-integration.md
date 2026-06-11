# Build: Cross-slice integration pass

Spec reference: `docs/spec-032-full_relay-0_0_9.md` (all seven slices final-accepted; this pass per BUILD.md "Cross-slice integration pass")
Status: final-accepted

## Integration pass (Worker 1)

Performed 2026-06-11, fresh spawn. All seven `bld-slice-*.md` artifacts read in full, in slice order (no "as needed"); every artifact's `What looks solid`, `DRY findings`, and `Notes for Worker 1` sections walked for deferred follow-ups. Spec status line (line 5) re-verified: "all seven slices implemented … build complete pending the cross-slice integration pass and the final test-run gate" — accurate for this pass; no edit.

### Static inspection confirmation (BUILD.md step 2)

Shadow output refreshed this pass with `uv run python scripts/review_inspect.py --all --output-dir docs/shadow` (every package `.py`) plus individual runs for the build-touched test/example files: `tests/test_relay_node_field.py`, `tests/test_relay_connection.py`, `tests/test_connection.py`, `tests/testing/test_relay.py`, `tests/types/test_base.py`, `tests/test_registry.py`, `tests/base/test_init.py`, `examples/fakeshop/tests/test_inspect_django_type.py`, `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/test_query/test_library_api.py`. Every Python file with review-worthy logic the build touched (`types/base.py`, `types/finalizer.py`, `types/definition.py`, `connection.py`, `relay.py`, `registry.py`, `testing/relay.py`, `testing/__init__.py`, the test files) has a current overview. No skips needed this pass; per-slice skips (e.g. `testing/__init__.py` docstring-only at Slice 5, `registry.py` ~12-line co-clear at Slice 2) were recorded in their slice artifacts with reasons and stand.

### Repeated string literals — cross-overview comparison (BUILD.md step 3)

Literals appearing in 2+ files (source side):

- **`"or inherit \`relay.Node\` directly."`** — byte-identical at **3 composed sites**: `types/base.py::_validate_connection` (base.py:202), `types/base.py` globalid gate (base.py:322, inside the `_RELAY_NODE_GATE_LEAD` f-string), `testing/relay.py::global_id_for` (testing/relay.py:76). The base.py overview shows it as a 2x in-file repeat; the testing/relay.py copy makes it cross-file. **This is the ledger's escalated priority hoist candidate (3rd copy reached at Slice 5) → MUST-FIX item 3 below.** The 2 parenthesized variants (`relay.py:137`, `connection.py:739` — `"(or inherit \`relay.Node\` directly)"`) are a different byte shape inside the fifth-guard messages and are NOT part of the hoist (see accepted deferral c).
- Meta-key vocabulary strings (`connection`, `relation_shapes`, `total_count`, `interfaces`, `order_by`, …) repeat across `types/base.py`, `connection.py`, and tests — these are key-name literals whose vocabulary IS single-sourced where it matters (`ALLOWED_META_KEYS`, `RELATION_SHAPE_VALUES`, `STRING_GLOBALID_STRATEGIES`); the remaining occurrences are dict keys/kwargs at use sites, the package's established pattern. No action.
- `GLOBALID_INVALID` — exactly once in source (`relay.py::_decode_or_graphql_error`); 3x in `tests/test_relay_node_field.py` pinning the wire contract (pre-cleared at Slice 2). No action.
- Test-side: `products.category` / `CategoryNode` / `pageInfo` / `hasNextPage` etc. repeat across `tests/test_relay_node_field.py`, `tests/testing/test_relay.py`, `tests/test_relay_connection.py`, and the live suite — the established inline-GraphQL-document and model-label idiom, accepted across Slices 2/4/5/6 reviews. One exception ruled MUST-FIX: the two fully-repeated GraphQL documents in `tests/test_relay_node_field.py` (7x / 6x) where the file ALREADY hoists `_NODE_QUERY` / `_NODES_QUERY` — see item 4.

### Imports — dependency-direction comparison (BUILD.md step 4)

Walked the Imports sections of all build-touched module overviews. One-way direction holds; no boundary violation:

- Top-level `relay.py` imports downward only (`exceptions`, `list_field`, `types.base`, `types.relay`) at module top. Nothing under `types/` imports top-level `relay.py` at module load: `types/finalizer.py`'s `from ..relay import _node_fields_declared` (finalizer.py:532) and `registry.py`'s co-clear import (registry.py:516) are function-local, per the documented cycle-safe precedent.
- `types/finalizer.py`'s `from ..connection import _build_relation_connection_resolver, _connection_type_for` (finalizer.py:319) is function-local, plain (non-best-effort) — the Slice-3 contract-step shape.
- `testing/relay.py` imports only from `types/base.py` / `types/relay.py` (absolute-path style matching `testing/__init__.py`); `testing/__init__.py` `__all__` is byte-unchanged (`["safe_wrap_connection_method"]`) — the Decision-10 export gate is intact.
- Cross-module private imports (`_RELAY_NODE_GATE_LEAD`, `_is_relay_shaped`, `_model_for`, `_validate_djangotype_target`) all follow the shipped private-sibling-import precedent (`relay.py` ← `types/relay.py::_model_for` etc.). The MUST-FIX gate-tail hoist (item 3) adds one name to an import line that already exists in `testing/relay.py` — no new boundary.

### Integration checks (BUILD.md step 6)

- **Duplicated helpers across slices:** none new. `_generate_connection_class` is single-sited (one `types.new_class` site in `connection.py`); the five `relay.py` module helpers each have ≥2 call sites; `_user_is_staff` hoisted at the 3rd-copy site (Slice 6); cardinality is single-sourced through `FieldMeta.is_many_side` at both the stage-2 validator and the synthesis loop. The one standing near-copy is ledger item (d), ruled below.
- **Naming / error-handling consistency:** coherent across slices — `ConfigurationError` for every config-time failure, `GraphQLError` only at the request boundary, exactly one extensions code (`GLOBALID_INVALID`), gate messages composed from `_RELAY_NODE_GATE_LEAD` with spec-pinned per-gate tails.
- **Repeated ORM/queryset patterns:** none to centralize. New ORM surfaces are each single-sited: `_coerce_pk_or_none`'s `pk.to_python`, the relation-manager seed `getattr(root, accessor).all()`, the `BookType.get_queryset` exclude.
- **Misplaced responsibilities:** none found; the decode seam, the connection pipeline, and the finalizer phases each own exactly the responsibilities the spec assigns.
- **Exports:** `django_strawberry_framework/__init__.py` gains exactly the two spec-named symbols (Slice 2, DoD item 4, pinned by `tests/base/test_init.py`); no other export drift; `testing` gate intact.
- **Comment coherence:** one stale sentence survives — MUST-FIX item 1. Anchor sweep clean: zero staged `TODO(spec-032 … Slice N)` anchors remain anywhere (remaining `TODO(spec-032` matches are the spec's own descriptive prose and `docs/feedback.md`'s descriptive scratch, both pre-cleared).

---

## Consolidation work list (Worker 0: dispatch Worker 2, then Worker 3)

### MUST-FIX items (exact fix specs)

Items 1–4 are source/test edits; items 5–6 are **DB-backed** (Django ORM via `manage.py shell`, then regenerate — NEVER hand-edit `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md`); item 7 is a `CHANGELOG.md` edit explicitly granted below.

1. **Stale module docstring (Slice-4 deferred Low — `tests/test_relay_node_field.py:8-9`).** The docstring still ends "The Slice-4 permission-integration additions below are staged." — false since Slice 4 removed the staged anchor and delivered the contract by citation. Fix: delete the sentence (or reword to past tense, e.g. "The Slice-4 permission-integration contract is satisfied by the Slice-2 tests below."). One-line edit.
2. **Trailing-comma layout violations on this build's diff lines.** `uv run python scripts/check_trailing_commas.py --check` reports 7 violations, ALL on lines this build added (Slice 3: `tests/types/test_base.py:371` collapse, `:385` explode, `:454` explode, `tests/test_relay_connection.py:357` explode; Slice 5: `tests/testing/test_relay.py:136` explode, `:160` collapse; Slice 4/6 block: `examples/fakeshop/test_query/test_library_api.py:2783` explode). Fix: run `uv run python scripts/check_trailing_commas.py` (default auto-fix), then `uv run ruff format .` and `uv run ruff check --fix .`; verify `--check` exits 0 and `git status --short` shows only the expected files; confirm the touched tests still pass focused (`--no-cov`).
3. **Gate-tail hoist — the 3x byte-identical `"or inherit \`relay.Node\` directly."` (ledger item a, escalated at Slice 5).** Add a module constant beside `_RELAY_NODE_GATE_LEAD` in `types/base.py` (suggested name `_RELAY_NODE_GATE_INHERIT_TAIL`; exact identifier at Worker 2's discretion) holding the tail literal, and recompose the three sites from it: `types/base.py::_validate_connection` (base.py:202), the globalid gate (base.py:322 — split the tail out of the f-string), and `testing/relay.py::global_id_for` (testing/relay.py:76 — extend the existing `from django_strawberry_framework.types.base import _RELAY_NODE_GATE_LEAD, …` import). Update the explanatory comment block at base.py:91 to name the tail constant. **Correctness check: byte-identical output** — the pinned tests (`tests/types/test_base.py::test_connection_key_requires_relay_node`, the globalid gate tests, `tests/testing/test_relay.py::test_global_id_for_non_node_raises`) must pass UNMODIFIED (the Slice-3 `_RELAY_NODE_GATE_LEAD` hoist precedent). Do NOT touch `_validate_relation_shapes` ("or remove the key." tail is spec-pinned different) or the parenthesized fifth-guard variants in `relay.py` / `connection.py`.
4. **Hoist the two repeated GraphQL documents in `tests/test_relay_node_field.py`** (ledger item e: 7x `"query ($ids: [ID!]!) { categories(ids: $ids) { name } }"`, 6x `"query ($id: ID!) { category(id: $id) { name } }"`). The file already hoists `_NODE_QUERY` / `_NODES_QUERY` for the interface-typed shapes; two more module constants (suggested `_CATEGORY_QUERY` / `_CATEGORIES_QUERY`) complete the file's own established pattern. Pure test-side mechanical replacement; the suite must pass unmodified in behavior (`uv run pytest tests/test_relay_node_field.py --no-cov`).
5. **Card-033 stale citation (DB-backed; Slice-7 final-verification dispatch item 1).** `KANBAN.md:186` (CardItem text on card **033**) reads "…the fakeshop products connections-only conversion tracked under `WIP-ALPHA-032-0.0.9` (fakeshop activation)…" — wrong twice (the id renders `DONE-032-0.0.9` now, and the products conversion is tracked under `TODO-BETA-051-0.1.5`). Fix: ORM-edit that card-033 `CardItem`'s text to "…tracked under `TODO-BETA-051-0.1.5` (fakeshop activation)…", then regenerate all three docs (step shared with item 6).
6. **Board-preamble cohort prose (DB-backed; Slice-7 final-verification dispatch item 2).** `KANBAN.md:64` (`BoardDoc` text) still frames the cohort as "in progress as four WIP cards" while listing three `DONE-*` ids. Fix: ORM-edit the BoardDoc sentence to the three-done-one-WIP shape, e.g. "…the Relay connection cohort is nearly complete — `DONE-030-0.0.9` (`DjangoConnectionField`, the central read-side primitive), `DONE-031-0.0.9` (Django-model-based GlobalID encoding), and `DONE-032-0.0.9` (the full Relay story) have shipped; `WIP-ALPHA-033-0.0.9` (connection-aware optimizer planning) remains in progress." Keep the version-bump and blocked-cards sentences byte-identical. After items 5–6: run `uv run python scripts/build_kanban_md.py`, `build_kanban_html.py`, `build_glossary_md.py`; re-run all three a second time and verify `git status --short` shows no further change (double-regenerate byte-clean); `uv run python examples/fakeshop/manage.py check` and `import_spec_terms --check` stay green.
7. **CHANGELOG `[spec-orders]` link-def re-relativization (Slice-7 review Low; Slice-7 final-verification dispatch item 4).** `CHANGELOG.md:281` — `[spec-orders]: docs/spec-028-orders-0_0_8.md` targets a file that lives at `docs/SPECS/spec-028-orders-0_0_8.md` (verified: the `docs/` path does not exist). Fix: re-relativize the def to `docs/SPECS/spec-028-orders-0_0_8.md` (the def belongs under the `<!-- docs/SPECS/ -->` group header per the START.md convention — move it there if it currently sits under `<!-- docs/ -->`). One-line(-ish), deterministic. **CHANGELOG-edit grant:** Worker 1's Slice-7 final verification explicitly ruled this fix in-cycle and dispatched it to the integration pass; this work-list entry IS the explicit instruction AGENTS.md requires. No other CHANGELOG content may be touched.

Worker 2 validation contract for the pass: `uv run ruff format .`, `uv run ruff check --fix .`, `scripts/check_trailing_commas.py --check` exit 0, focused `--no-cov` runs for the touched test files (`tests/types/test_base.py tests/testing/test_relay.py tests/test_relay_node_field.py tests/test_relay_connection.py examples/fakeshop/test_query/test_library_api.py`), the item-6 regenerate/byte-clean/`manage.py check` block, and the usual `git status --short` classification. Worker 3 reviews the consolidation diff (byte-identity of the recomposed gate messages, DB-edit purity of the regenerated files, no behavior change anywhere).

### Accepted deferrals and closed rulings (with reasons)

- **(b) 2x `".Meta.interfaces entry "` f-string prefix (`types/base.py:894/910`) — CLOSED, accepted.** Never reached a 3rd occurrence (Slice 3's messages use the `{Model}.Meta.relation_shapes` subject shape, re-verified this pass). A constant for a 2x 24-character f-string prefix hurts readability more than it saves — consistent with the Slice-1/3 reasoning. Re-open only if a future gate adds a 3rd `…Meta.interfaces entry…` raise.
- **(c) Fifth-guard "Relay-Node-shaped DjangoType" wording at 2 sites (`connection.py:738`, `relay.py:136`) — ACCEPTED deferral.** The two messages have distinct subjects (a connection field vs the named node-field factory + "target"); `connection.py`'s text is shipped `DONE-030` wording; a cross-module one-noun parameterization buys no consolidation value; and `WIP-ALPHA-033-0.0.9` works in `connection.py` next, so any hoist is better weighed there. The shared parenthesized tail is 2x only (below the 3rd-copy rule).
- **(d) `_build_relation_connection_resolver` near-copies `_build_connection_resolver`'s sync branch (Slice-3 Low, re-ruled here as the Slice-3 final verification mandated) — ACCEPTED deferral to `WIP-ALPHA-033-0.0.9`.** Re-examined with all seven slices' evidence: the duplication is ~10 mechanical lines; the spec's Decision 6 pins the standalone-helper shape; the 2-line seed-lambda delegation would route a framework-synthesized resolver through the consumer-resolver branch (semantic mislabel, pointless `_is_async_callable` run) and strand the helper's load-bearing docstring contract (033 prefetch-cache seam, `many_resolver` accessor-identity pin, strictness-blind posture). 033 wires strictness/planning into the connection pipeline and may genuinely diverge the two builders — consolidating now risks immediate un-consolidation. **Re-rule at 033's build**; carry to `bld-final.md`'s deferred-work catalog.
- **(f) 4x `"global_id_for: "` message prefix in `testing/relay.py` — CLOSED, accepted** (re-confirmed at exactly 4 this pass). All four sites live inside one ~40-line function; no second module would ever import a 15-character prefix constant. Slice-5 ruling stands.
- **(g) Opted/bare connection description asymmetry (`connection.py` — opted `<TypeName>Connection` classes ship description-less via `description=None` at connection.py:275; the bare path preserves the inherited Strawberry description at :355) — ACCEPTED deferral, watch only.** Both shapes are shipped SDL surface; adding a description to the opted classes would churn shipped opted SDL for zero consumer value. Revisit only if a future card deliberately normalizes connection SDL.
- **Test-file inline-GraphQL-document idiom** (live suite + `tests/test_relay_connection.py` `pageInfo`/`hasNextPage` fragments, model-label literals, file-local `_make_node_type`-family helper copies ≤10 lines) — **CLOSED, accepted**: the suites' established per-file-self-contained pattern, pre-cleared repeatedly across Slices 2–6. Item 4 above is the one exception (an in-file pattern the file itself already established and then stopped applying).
- **TREE.md target-tree `test_wrap.py` back-fill** (Slice-7 final-verification item 3's optional note) — **ACCEPTED deferral**: pre-existing drift (the missing mirror predates this card); optional one-liner for the next doc-touching card; not worth a DB-free doc edit in this consolidation pass.
- **One-off `tests/types/test_definition_order_schema.py::test_relay_declared_type_emits_node_interface_and_global_id` flake** (Slice-3 Low) — not integration work; **carried as the recorded watchpoint for the final test-run gate** (`bld-final.md`): if it recurs in the full `--no-cov` sweep, treat as a real flake and bisect; if clean, write off as transient.

### Spec changes made (Worker 1 only)

None this pass. The spec status line is current ("build complete pending the cross-slice integration pass and the final test-run gate"); every consolidation item above is build-hygiene or pre-existing-drift repair, none changes a spec contract. `check_spec_glossary.py` not re-run (no spec edit).

### Re-run plan

After Worker 2's consolidation pass (`Status: built`) and Worker 3's review (`Status: review-accepted`), Worker 0 re-dispatches Worker 1 to re-run this integration pass (verify the 7 items landed: grep counts — gate-tail composed sites read from one constant, doc literals hoisted, `check_trailing_commas --check` exit 0, `KANBAN.md:186`/`:64` fixed and byte-clean regenerated, `[spec-orders]` def resolves, stale docstring gone) and flip this artifact to `final-accepted`, unblocking the final test-run gate (`bld-final.md`).

---

## Build report (Worker 2, integration consolidation)

Performed 2026-06-11, fresh spawn. Executed the 7-item FIX-NOW work order from Worker 1's integration pass exactly; the DEFER items (b/c/d/f/g, TREE.md back-fill, the `test_definition_order_schema` flake watchpoint) were not touched.

### Files touched

- `django_strawberry_framework/types/base.py` — **item 3.** Added module constant `_RELAY_NODE_GATE_INHERIT_TAIL = "or inherit \`relay.Node\` directly."` beside `_RELAY_NODE_GATE_LEAD`; recomposed the two in-module sites (`_validate_connection`'s connection gate, the globalid gate in `_validate_globalid_strategy`) from it. Updated the explanatory comment block to name the new constant. `_validate_relation_shapes`' "or remove the key." tail left inline (spec-pinned different shape).
- `django_strawberry_framework/testing/relay.py` — **item 3.** Extended the existing `from django_strawberry_framework.types.base import (...)` to also import `_RELAY_NODE_GATE_INHERIT_TAIL` (pre-sorted: it sorts before `_RELAY_NODE_GATE_LEAD`); recomposed `global_id_for`'s third gate-tail site from it.
- `tests/test_relay_node_field.py` — **items 1 + 4.** Item 1: reworded the stale module docstring sentence to "The Slice-4 permission-integration contract is satisfied by the Slice-2 tests below." Item 4: added `_CATEGORY_QUERY` / `_CATEGORIES_QUERY` module constants beside the existing `_NODE_QUERY`, replaced all 6 `category(id:)` and 7 `categories(ids:)` inline document literals with the constants.
- `tests/types/test_base.py`, `tests/test_relay_connection.py`, `tests/testing/test_relay.py`, `examples/fakeshop/test_query/test_library_api.py` — **item 2.** Trailing-comma layout fixed by `scripts/check_trailing_commas.py` (default auto-fix; 4 files reformatted). All 7 reported violations were on lines this build added (Slices 3/4/5/6) as Worker 1 noted.
- `CHANGELOG.md` — **item 7** (explicit grant). Moved `[spec-orders]` link def out of the `<!-- docs/ -->` group and into `<!-- docs/SPECS/ -->` (alphabetical, after `[spec-filters]`), re-relativized `docs/spec-028-orders-0_0_8.md` → `docs/SPECS/spec-028-orders-0_0_8.md`. Disk-exists confirmed: the `docs/` path does not exist; `docs/SPECS/spec-028-orders-0_0_8.md` does. No other CHANGELOG content touched.
- `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` — **items 5 + 6, DB-backed.** Regenerated outputs of two ORM edits to `examples/fakeshop/db.sqlite3` (never hand-edited).
- `examples/fakeshop/db.sqlite3` — **items 5 + 6.** ORM edits via `manage.py shell`: (5) `CardItem` id=944 (card-033, "Other" section, order 10) text `\`WIP-ALPHA-032-0.0.9\` (fakeshop activation)` → `\`TODO-BETA-051-0.1.5\` (fakeshop activation)`; (6) `BoardDoc(namespace="kanban", key="snapshot")` body cohort sentence reshaped from "in progress as four WIP cards — …" to "nearly complete — … have shipped; `{{card_ref:19}}` (…) remains in progress.", preserving every `{{card_ref:N}}` placeholder and the byte-identical version-bump and blocked-cards sentences. Edits used assert-count-then-replace (`count(old)==1`, `count(new)==0`) inside one `transaction.atomic()`.

### Validation run

- `scripts/check_trailing_commas.py` (default auto-fix) — 4 files reformatted; follow-up `--check` exits 0.
- `uv run ruff format .` — 241 files left unchanged (the checker had already formatted the 4 fixed files). The COM812-conflict warning is the standard repo warning (AGENTS.md: COM812 only auto-adds to already-multi-line constructs), not a new condition.
- `uv run ruff check --fix .` — All checks passed.
- `git status --short` — modified set is byte-identical to the task-start baseline (no NEW files appeared from this pass; my edits landed inside files already in the prior-slice diff). Prior slices' diffs intact; the `??` untracked `bld-slice-*.md` / `build-*.md` artifacts are this build's own files. No tool-churn revert needed.
- `uv run python examples/fakeshop/manage.py check` — System check identified no issues (0 silenced).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — OK: 32 done cards have glossary links.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md` — GREEN: 40 terms, all with glossary entries and ≥1 spec link.
- Double-regenerate byte-clean: md5 of `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` identical across two consecutive full regenerate runs (no drift after the second regenerate).
- Gate-tail byte-identity proof (item 3 correctness check): reconstructed the connection and globalid gate strings from the two constants and asserted `==` against the shipped `… or inherit \`relay.Node\` directly.` form — both `True`. The pinned tests (`test_connection_key_requires_relay_node`, the globalid gate tests, `test_global_id_for_non_node_raises`) pass UNMODIFIED.
- Focused tests (`--no-cov`): `uv run pytest tests/types/test_base.py tests/testing/test_relay.py tests/test_relay_node_field.py tests/test_relay_connection.py examples/fakeshop/test_query/test_library_api.py --no-cov` → **248 passed**.

### Implementation notes

- **Item 3 constant identifier.** Chose `_RELAY_NODE_GATE_INHERIT_TAIL` (the work order's suggested name) — sits directly below `_RELAY_NODE_GATE_LEAD` and reads as the matching tail. The connection/globalid first literals keep their trailing space (`… {_RELAY_NODE_GATE_LEAD} `) so the f-string concatenation reproduces the single inter-word space byte-for-byte; the tail constant carries no leading space.
- **Item 4 constant placement.** Defined both `_CATEGORY_QUERY` and `_CATEGORIES_QUERY` immediately after `_NODE_QUERY` (module top) rather than splitting them to mirror the `_NODES_QUERY` location — the `categories(ids:)` document is first used at the typed-single-node section (well before `_NODES_QUERY`'s definition point), so a single co-located block is the only placement where both constants are defined before first use. Matches the file's existing `_NODE_QUERY`-at-top idiom.
- **Item 6 placeholder preservation.** The board-preamble cohort prose stores `{{card_ref:N}}` placeholders, not rendered card-id strings. The work order's target wording (`DONE-030-0.0.9` … `WIP-ALPHA-033-0.0.9`) is the *rendered* form; the ORM edit reshapes only the prose around the unchanged placeholders, so the renderer emits exactly the target sentence. No `card_references` edge or placeholder index was altered.
- **Item 5/7 id confirmation.** The fix from `WIP-ALPHA-032-0.0.9` → `TODO-BETA-051-0.1.5` is corroborated by four pre-existing correct `TODO-BETA-051-0.1.5` references already in the rendered `KANBAN.md` (the canonical id for the fakeshop-activation card). The `[spec-orders]` re-relativization target was disk-verified before and after.

### Notes for Worker 3

- Review surface: byte-identity of the recomposed gate messages (proof recorded above; the three composed sites now read the two `types/base.py` constants), DB-edit purity of the regenerated docs (no hand-edit; double-regenerate md5-stable), and no behavior change anywhere (248 focused tests green, all pinned tests unmodified).
- The `git diff HEAD` for `types/base.py` shows `_validate_relation_shapes` ("relation_shapes … or remove the key.") changes too — those are **Slice 3's** already-shipped `_RELAY_NODE_GATE_LEAD` hoist, NOT this pass. This pass left that gate's distinct tail inline; only `_RELAY_NODE_GATE_INHERIT_TAIL` (lines ~91/101/208/328) and the comment update are mine in that file.
- The parenthesized fifth-guard variants in `relay.py:137` / `connection.py:739` (`(or inherit \`relay.Node\` directly)`) are intentionally untouched (accepted deferral c; different byte shape).
- `examples/fakeshop/db.sqlite3` is git-tracked; both ORM edits are idempotent (assert-count-then-replace) and ran in one atomic transaction.

---

## Review (Worker 3, integration consolidation)

Performed 2026-06-11, fresh spawn. Reviewed ONLY the consolidation delta (Worker 2's 7-item FIX-NOW execution) against Worker 1's FIX-NOW work order, using `### Files touched` as the cumulative-diff navigational filter. Every claim below independently verified — no acceptance by report alone.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **Gate-tail hoist (item 3) — verified byte-identical.** Imported `_RELAY_NODE_GATE_LEAD` + `_RELAY_NODE_GATE_INHERIT_TAIL` under `django.setup()` and reconstructed all three composed messages. `f"{lead} {tail}"` == the historical inline literal `"requires a Relay-Node-shaped type; add \`relay.Node\` to \`Meta.interfaces\` or inherit \`relay.Node\` directly."` exactly (`== True`). `_RELAY_NODE_GATE_LEAD` carries no trailing space; each compose site re-inserts the single inter-word space via the f-string (`{lead} {tail}`); the tail constant carries no leading space — concatenation reproduces the shipped byte sequence. The three sites: `types/base.py::_validate_connection` (base.py #"_validate_connection"), the globalid gate in `_validate_globalid_strategy` (base.py #"is_meta and not relay_shaped"), and `testing/relay.py::global_id_for` (testing/relay.py #"global_id_for: {definition.graphql_type_name} {_RELAY_NODE_GATE_LEAD}"). The `review_inspect.py` overview for base.py no longer lists `"or inherit \`relay.Node\` directly."` as a repeated literal — single-sourced. Distinct tails correctly left inline: `_validate_relation_shapes`' `"or remove the key."` (base.py #"or remove the key.") and the parenthesized fifth-guard variants `"(or inherit \`relay.Node\` directly)"` at `relay.py:137` / `connection.py:739` (different byte shape — confirmed both still present, untouched; neither file is in the consolidation `Files touched`).
- **GraphQL-doc hoist (item 4) — verified exact substitution.** `_CATEGORY_QUERY = "query ($id: ID!) { category(id: $id) { name } }"` and `_CATEGORIES_QUERY = "query ($ids: [ID!]!) { categories(ids: $ids) { name } }"` (tests/test_relay_node_field.py #"_CATEGORY_QUERY"). The literal text now appears exactly once each in the file — only on the definition lines; every prior inline use (the work-order's 6x / 7x) is now a constant reference. No query-text drift. Completes the file's own pre-existing `_NODE_QUERY` / `_NODES_QUERY` hoist idiom.
- No new duplication introduced by the consolidation. The `testing/relay.py` import line gains exactly one name (`_RELAY_NODE_GATE_INHERIT_TAIL`, pre-sorted before `_RELAY_NODE_GATE_LEAD` — ASCII `INHERIT` < `LEAD`) on an import that already existed — no new module boundary.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows ONLY Slice-2's spec-authorized exports (`DjangoNodeField` / `DjangoNodesField`, DoD items 3-4) — this is cumulative-diff content, NOT consolidation work (`__init__.py` is not in Worker 2's `Files touched`). The consolidation pass did not touch the public surface. `__version__` stays `0.0.8` (joint-cut boundary, spec Decision 13). No new export drift from this pass.

### CHANGELOG sanity

The consolidation touched `CHANGELOG.md` for item 7 ONLY (explicit per-card grant recorded in the work order). Verified the delta is exactly the `[spec-orders]` link-def move: removed `[spec-orders]: docs/spec-028-orders-0_0_8.md` from under `<!-- docs/ -->`, added `[spec-orders]: docs/SPECS/spec-028-orders-0_0_8.md` under `<!-- docs/SPECS/ -->` (alphabetical, after `[spec-filters]`). Disk-exists confirmed both ways: `docs/SPECS/spec-028-orders-0_0_8.md` exists; `docs/spec-028-orders-0_0_8.md` does not. Reference-style convention upheld (START.md "Markdown link convention"). The remaining `CHANGELOG.md` hunks in `git diff HEAD` (the `### Added` Relay bullets, the `### Changed` latent→live reword, the staged-anchor removal, the `[glossary-get_queryset-visibility-hook]` def) are Slice-7's already-accepted contribution, not this pass — no other CHANGELOG content was modified by the consolidation.

### Documentation / release sanity

- **Card-033 citation (item 5, DB-backed) — fixed.** `KANBAN.md` card-033 CardItem now reads "…tracked under `TODO-BETA-051-0.1.5` (fakeshop activation)…"; zero `WIP-ALPHA-032` occurrences remain anywhere in `KANBAN.md`.
- **Board-preamble cohort prose (item 6, DB-backed) — fixed.** `KANBAN.md` board preamble now reads the three-done-one-WIP shape: `DONE-030-0.0.9` / `DONE-031-0.0.9` / `DONE-032-0.0.9` "have shipped"; `WIP-ALPHA-033-0.0.9` "remains in progress." The version-bump and blocked-cards sentences are intact.
- **Regenerated, not hand-edited — verified byte-stable.** Re-ran `build_kanban_md.py`, `build_kanban_html.py`, `build_glossary_md.py`; md5 of `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` identical before and after regeneration (regenerate produced no change vs the working tree). Source-of-truth check: the `BoardDoc(namespace="kanban", key="snapshot")` body stores `{{card_ref:14/16/17/18/19}}` + `{{active_version}}` placeholders (NOT rendered card-id strings) — all preserved; the renderer resolves them to the target IDs. So the edit is a genuine ORM-then-regenerate, not a hand-edit of rendered markdown.
- **DONE-032-0.0.9** appears in the `## Done` section exactly once (the card detail at `KANBAN.md` #"DONE-032-0.0.9 - Full Relay story" heading), all 11 Definition-of-Done items ticked `- [x]`. (The card-detail "Status: Planned" metadata line is pre-existing card-body rendering outside the consolidation scope — Worker 2 edited only the card-033 CardItem and the board preamble; not a finding for this pass.)
- `manage.py check` clean; `import_spec_terms --check` OK (32 done cards have glossary links); `check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md` GREEN (40 terms, all with glossary entries and ≥1 spec link).

### What looks solid

- The gate-tail hoist is a textbook 3rd-copy single-source consolidation: byte-identity proven programmatically, the distinct tails (`"or remove the key."`, the parenthesized fifth-guard) correctly excluded, the explanatory comment block at base.py #"_RELAY_NODE_GATE_LEAD shared by the three" names the new constant and spells out exactly what stays inline and why.
- Pure-consolidation discipline held: no error-message text changed (all three messages reconstruct byte-identically), no control flow touched, no behavior change. The pinned diagnostic tests pass UNMODIFIED — `test_connection_key_requires_relay_node` (tests/types/test_base.py:343 asserts the full inline tail), the relation-shapes matrix non-relay case (test_base.py:450-451 still asserts `"or remove the key."`), the globalid gate test (test_base.py:736 match="relay.Node"), and `test_global_id_for_non_node_raises` (tests/testing/test_relay.py:201).
- DB-edit purity: idempotent assert-count-then-replace in one atomic transaction, placeholders preserved, double-regenerate md5-stable. This is the correct shape for a DB-backed doc edit.
- Trailing-comma autofix (item 2) is layout-only: the parametrize tuple `("model", "fields", "relation_shapes", "relay_node", "expected")` and the `_encoder(type_cls, model, root, info)` signature exploded one-per-line per the ≥-threshold rule; no semantic change. `check_trailing_commas.py --check` exits 0.
- Item-1 docstring reword: `tests/test_relay_node_field.py` module docstring now reads "The Slice-4 permission-integration contract is satisfied by the Slice-2 tests below." — stale "staged" wording gone.

### Temp test verification

None created. This consolidation is verifiable by programmatic byte-identity (gate-tail reconstruction under `django.setup()`), exact-substitution grep (query constants), md5 double-regenerate stability (DB-backed docs), and the focused `--no-cov` suite. A temp test would not add signal over the byte-identity proof plus the 248-pass run. Disposition: not needed.

### Notes for Worker 1 (spec reconciliation)

None. No spec contract is affected; every consolidation item is build-hygiene or pre-existing-drift repair. Worker 1's integration pass already recorded "No spec changes this pass" and the spec status line is current.

### Verification runs (this review)

- `uv run pytest tests/test_relay_node_field.py tests/types/test_base.py tests/testing/test_relay.py tests/test_relay_connection.py examples/fakeshop/test_query/test_library_api.py --no-cov` → **248 passed** (matches Worker 2's report).
- `uv run python examples/fakeshop/manage.py check` → System check identified no issues (0 silenced).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → OK: 32 done cards have glossary links.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md` → GREEN: 40 terms.
- `uv run python scripts/check_trailing_commas.py --check` → exit 0 (clean).
- Double-regenerate byte-stability: md5 of `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` identical pre/post `build_kanban_md.py` + `build_kanban_html.py` + `build_glossary_md.py`.
- `scripts/review_inspect.py django_strawberry_framework/types/base.py --output-dir docs/shadow` → ran clean; walked the touched region (the two new constants + the recomposed `_validate_connection` / globalid gates); the gate-tail literal no longer surfaces as a repeated literal.
- Gate-tail byte-identity reconstruction under `django.setup()`: `_RELAY_NODE_GATE_LEAD + " " + _RELAY_NODE_GATE_INHERIT_TAIL == "requires a Relay-Node-shaped type; add \`relay.Node\` to \`Meta.interfaces\` or inherit \`relay.Node\` directly."` → `True`.

### Review outcome

`review-accepted`. The consolidation executed all 7 FIX-NOW items exactly per the work order with zero behavior change; the gate-tail hoist is byte-identical at all three compose sites and the distinct tails were correctly left inline; the GraphQL-doc hoist is an exact substitution; the DB-backed KANBAN fixes are genuine ORM-then-regenerate edits (placeholders preserved, double-regenerate byte-stable, DONE-032 intact); the CHANGELOG link-def move is the only CHANGELOG delta and resolves on disk. No High / Medium / Low findings. Status set to `review-accepted`.

---

## Integration re-verification (Worker 1)

Performed 2026-06-11, fresh spawn. Confirms Worker 2's consolidation (`built`) and Worker 3's review (`review-accepted`) cleared every cross-slice finding from the FIX-NOW work order. Spec status line (line 5) re-read — "all seven slices implemented … build complete pending the cross-slice integration pass and the final test-run gate" — still accurate; no spec edit this pass.

### FIX-NOW confirmation (all 7 landed)

- **Item 1 — stale docstring.** `tests/test_relay_node_field.py` module docstring now reads "The Slice-4 permission-integration contract is satisfied by the Slice-2 tests below." The false "…below are staged." sentence is gone. CONFIRMED.
- **Item 2 — trailing-comma layout.** `uv run python scripts/check_trailing_commas.py --check` exits 0 (the 7 build-added violations are fixed). CONFIRMED.
- **Item 3 — gate-tail hoist (byte-identity spot-check).** `_RELAY_NODE_GATE_INHERIT_TAIL = "or inherit \`relay.Node\` directly."` defined at `types/base.py:101` beside `_RELAY_NODE_GATE_LEAD`; composed at the three sites — connection gate (`base.py:207-208`), globalid gate (`base.py:328`), and `testing/relay.py::global_id_for` (`testing/relay.py:76-77`, importing the tail at `:41`, pre-sorted before `_RELAY_NODE_GATE_LEAD`). Programmatic byte-identity under `django.setup()`: `f"{_RELAY_NODE_GATE_LEAD} {_RELAY_NODE_GATE_INHERIT_TAIL}" == "requires a Relay-Node-shaped type; add \`relay.Node\` to \`Meta.interfaces\` or inherit \`relay.Node\` directly."` → `True`. The distinct `"or remove the key."` relation-shapes tail (`base.py:256`, still composed from LEAD only) and the parenthesized fifth-guard variants (`relay.py:137`, `connection.py:739`) are correctly left inline (DEFER c). The explanatory comment block (`base.py:91-99`) names the new tail constant and spells out what stays inline. CONFIRMED.
- **Item 4 — GraphQL-doc hoist.** `_CATEGORY_QUERY` / `_CATEGORIES_QUERY` defined once each (`tests/test_relay_node_field.py:78-79`); the raw inline query text now appears exactly once per document (the def line only) — every prior 6x/7x inline use is a constant reference. CONFIRMED.
- **Item 5 — card-033 stale citation (DB-backed).** Rendered `KANBAN.md:186` now reads "tracked under `TODO-BETA-051-0.1.5` (fakeshop activation)"; zero `WIP-ALPHA-032` occurrences remain anywhere in `KANBAN.md`. CONFIRMED.
- **Item 6 — board-preamble cohort prose (DB-backed).** Rendered `KANBAN.md:64` reads the three-done-one-WIP shape (`DONE-030-0.0.9` / `DONE-031-0.0.9` / `DONE-032-0.0.9` "have shipped"; `WIP-ALPHA-033-0.0.9` "remains in progress"); version-bump and blocked-cards sentences intact. CONFIRMED.
- **Items 5+6 regenerated-not-hand-edited proof.** Captured md5 of `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md`, re-ran `build_kanban_md.py` + `build_kanban_html.py` + `build_glossary_md.py`, re-captured md5 — all three identical (byte-stable). A hand-edit would have been reverted by the regenerate; the working-tree files ARE the DB render. CONFIRMED.
- **Item 7 — CHANGELOG `[spec-orders]` re-relativization.** `CHANGELOG.md:286` reads `[spec-orders]: docs/SPECS/spec-028-orders-0_0_8.md` under the `<!-- docs/SPECS/ -->` group; disk-exists confirmed both ways (`docs/SPECS/spec-028-orders-0_0_8.md` exists; `docs/spec-028-orders-0_0_8.md` does not). CONFIRMED.

### DEFER items confirmed untouched

- **(b)** `.Meta.interfaces entry ` prefix still 2x in `types/base.py` (below the 3rd-copy threshold) — not hoisted.
- **(c)** Parenthesized fifth-guard `"(or inherit \`relay.Node\` directly)"` still present at `relay.py:137` and `connection.py:739` (different byte shape) — not touched by the gate-tail hoist.
- **(d)** `_build_connection_resolver` (`connection.py:581`) and `_build_relation_connection_resolver` (`connection.py:649`) remain distinct standalone helpers — no seed-lambda delegation; deferred to `WIP-ALPHA-033-0.0.9`.
- **(f)** `global_id_for: ` prefix still 4x inline in `testing/relay.py` (one-function-local) — not extracted.
- **(g)** opted/bare connection-description asymmetry — watch-only, untouched.
- TREE.md target-tree `test_wrap.py` back-fill (pre-existing drift) and the `test_definition_order_schema` flake watchpoint — untouched; carried below.

### Sanity-check run (this re-verification)

- `uv run python examples/fakeshop/manage.py check` → System check identified no issues (0 silenced).
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → OK: 32 done cards have glossary links.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md` → GREEN: 40 terms, all with glossary entries and ≥1 spec link.
- `uv run python scripts/check_trailing_commas.py --check` → exit 0 (clean).
- `uv run pytest tests/test_relay_node_field.py tests/types/test_base.py tests/testing/test_relay.py --no-cov` → **145 passed** (the pinned gate-tail and GraphQL-doc tests pass unmodified).
- `git status --short` → modified set is byte-consistent with the consolidation report; no NEW files beyond this build's own `bld-*.md` / `build-*.md` artifacts; `pyproject.toml` / `__version__` / `uv.lock` correctly absent (joint-cut boundary, Decision 13).

### Deferred-work list carried to `bld-final.md`'s deferred-work catalog

This list is the seed for the final gate's `### Deferred work catalog`:

- **Relation-resolver near-copy → `WIP-ALPHA-033-0.0.9`** (ledger d, integration `### Accepted deferrals`): `_build_relation_connection_resolver` near-copies `_build_connection_resolver`'s sync branch (~10 mechanical lines); Decision 6 pins the standalone-helper shape, and 033 may genuinely diverge the two builders when it wires strictness/planning into the connection pipeline. Re-rule at 033's build.
- **`.Meta.interfaces entry ` 2x f-string prefix (ledger b)** — accepted; re-open only if a future gate adds a 3rd `…Meta.interfaces entry…` raise.
- **Fifth-guard "Relay-Node-shaped DjangoType" wording, 2 sites (ledger c) → weigh at `WIP-ALPHA-033-0.0.9`** — `connection.py:738` is shipped `DONE-030` wording; 033 works in `connection.py` next, so any cross-module parameterization is better weighed there.
- **`global_id_for: ` 4x message prefix (ledger f)** — accepted closed; one-function-local, no second importer.
- **Opted/bare connection-description asymmetry (ledger g)** — watch-only; revisit only if a future card deliberately normalizes connection SDL.
- **TREE.md target-tree `test_wrap.py` back-fill** (Slice-7 final-verification item 3) — pre-existing drift predating this card; optional one-liner for the next doc-touching card.
- **`tests/types/test_definition_order_schema.py::test_relay_declared_type_emits_node_interface_and_global_id` flake** (Slice-3 Low) — final-test-run-gate watchpoint: if it recurs in the full `--no-cov` sweep, bisect as a real flake; if clean, write off as transient.

### Spec changes made (Worker 1 only)

None this pass. The spec status line is current; every confirmed item is build-hygiene or pre-existing-drift repair, none changes a spec contract. `check_spec_glossary.py` re-run as a sanity check (no spec edit), GREEN at 40 terms.

### Re-verification outcome

`final-accepted`. The consolidation cleared every cross-slice finding: all 7 FIX-NOW items landed and verified (gate-tail byte-identical, GraphQL docs single-sourced, trailing commas clean, both DB-backed KANBAN fixes byte-stable-regenerated, CHANGELOG link-def resolved, stale docstring reworded); all DEFER items left untouched; the four sanity checks are GREEN and the focused suite passes. The integration pass is closed; the final test-run gate (`bld-final.md`) is unblocked.
