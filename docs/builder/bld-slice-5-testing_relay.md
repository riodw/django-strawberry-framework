# Build: Slice 5 — public `testing/relay.py` helpers (Decision 10)

Spec reference: `docs/spec-032-full_relay-0_0_9.md` (lines 104-106 slice checklist; Decision 10 lines 443-459; Decision 11 lines 461-464 file placement; Test plan Slice-5 lines 584-589; Revision 2 P2 line 40 — the secondary-emitter decode asymmetry is the documented contract; Revision 7 P3 lines 18 + 543 — `global_id_for` reads the finalize-stamped `effective_globalid_strategy`; impl-plan table line 506; DoD item 8 lines 674-676)
Status: final-accepted

## Plan (Worker 1)

Spec status-line re-verification (per worker-1.md): spec line 5 reads "Slices 1–4 implemented … Slices 5–7 not started" — accurate at this planning pass; no edit needed.

Staged `TODO(spec-032 … Slice 5)` anchors this slice ships and removes (grep-verified; the slice removes its own anchors per the AGENTS.md design-doc discipline, in the same change that ships the code):

- `django_strawberry_framework/testing/relay.py:15` — "Strategy-aware id mint." pseudocode block (the whole staged comment body, including the asymmetry-contract paragraph at lines 28-33, is replaced by the real implementation).
- `django_strawberry_framework/testing/relay.py:35` — "Public decode re-export." block.
- `django_strawberry_framework/testing/__init__.py:34` — the docstring-only-edit anchor (the anchor itself prescribes the Slice-5 edit shape: docstring pointer, NO re-export).
- `tests/testing/test_relay.py:9` — the staged test list (replaced by the real suite).

No other slice's anchors are touched (Slice 6 anchors in `apps/library/schema.py:61,336` + `test_query/test_library_api.py:2533`, Slice 7 anchors in `docs/README.md:118`, `docs/GLOSSARY.md:357`, `docs/TREE.md:193` stay as-is).

Static inspection (`scripts/review_inspect.py … --output-dir docs/shadow`):

- `django_strawberry_framework/types/relay.py` — RUN (923 lines, under `types/`; the encode/decode + strategy-stamping seam this slice consumes). Shadow at `docs/shadow/django_strawberry_framework__types__relay.{overview.md,stripped.py}`. Repeated-literals section shows no literal this slice would add a copy of (`decode_global_id:` 3x stays internal; the helper introduces no new copy because it re-exports rather than wraps).
- `django_strawberry_framework/testing/__init__.py` — SKIPPED with reason: 40 lines, pure re-export + docstring; this slice's edit is docstring-only (no review-worthy logic; BUILD.md skip allowance).
- `django_strawberry_framework/testing/relay.py` — SKIPPED at planning with reason: currently statement-free (docstring + staged comments only — nothing to inspect). Worker 3 must run the helper on it post-build (new `.py` file with logic; BUILD.md Worker-3 trigger).
- `tests/testing/test_relay.py` — SKIPPED with reason: currently statement-free staged stub; test files are not under the Worker-1 mandatory triggers.

### DRY analysis

- **Existing patterns reused (the helper must NOT re-derive payloads):**
  - `django_strawberry_framework/types/relay.py::encode_typename` (lines 415-455) — the single strategy→payload-slot mapping (spec-031 Decision 4): `model` / `type+model` → `definition.model._meta.label_lower`, `type` → `definition.graphql_type_name`. `global_id_for` calls it with `(definition, strategy, type_cls, None, None)` — for the three string strategies the function never touches `root` / `info` (only the `callable` branch does, and `global_id_for` rejects `callable` / `custom` before the call), so the helper's payload is computed by the exact code path the live closure runs (`_install_typename_closure` line 589-590 calls the same function). Re-typing `label_lower` / `graphql_type_name` in `testing/relay.py` is forbidden — it would fork the mapping `MODEL_LABEL_STRATEGIES` (types/relay.py:375) exists to centralize.
  - `django_strawberry_framework/types/relay.py::decode_global_id` (lines 596-709) — re-exported as-is (`from …types.relay import decode_global_id`), per the spec's "the internal helper's signature is already consumer-shaped" (Decision 10). NO wrapper function: a wrapper would duplicate the docstring contract and add a stack frame for nothing.
  - `definition.effective_globalid_strategy` — the finalize-stamped classification (`types/relay.py::install_globalid_typename_resolver` step 3, line 567; slot documented at `types/definition.py:146` and its invariants docstring). Reading the stamp (never re-reading `RELAY_GLOBALID_STRATEGY` via `_resolve_globalid_strategy`) is what makes the helper consistent-by-construction with live emission (spec Revision 7 P3 / Test-plan line 543). The stamp also doubles as the finalized-Relay-Node gate: `None` ⇒ unfinalized or non-Node.
  - `django_strawberry_framework/types/base.py::STRING_GLOBALID_STRATEGIES` (line 104) — the `{"model", "type", "type+model"}` membership for the "deterministically encodable" test. The complement IS the `callable` / `custom` rejection: types/relay.py (lines 365-374) deliberately has no `{"callable", "custom"}` literal anywhere ("their absence from both memberships IS the contract"), and this slice must not introduce the first one.
  - `django_strawberry_framework/types/base.py::_RELAY_NODE_GATE_LEAD` (line 95) — the Slice-3-hoisted Relay-gate wording ("requires a Relay-Node-shaped type; add `relay.Node` to `Meta.interfaces`") for the non-Node rejection message; this is the 4th recomposition site (precedent: 3 byte-identical sites verified at Slice 3 final verification). Cross-module private import has the shipped precedent of `relay.py:51` importing `_model_for` from `types/relay.py`.
  - `str(relay.GlobalID(type_name=payload, node_id=str(id)))` — Strawberry's own base64 encoding (`strawberry/relay/types.py::GlobalID.__str__`; verified against the locked 0.316.0: `str()` emits the base64 `from_id` parses). Mirrors the shipped `tests/test_relay_node_field.py::_gid` helper shape.
  - Test fixtures: `tests/types/test_relay_interfaces.py::_isolate_registry` (lines 40-45) + `tests/test_relay_node_field.py::_isolate_registry` (the autouse `registry.clear()` bracket), `tests/test_relay_node_field.py::_make_node_type` / `_schema_with` (inline Relay-shaped types over `apps.products` models + minimal `strawberry.Schema(config=strawberry_config())`), `tests/types/test_relay_interfaces.py::_build_multi_type` (lines 1628-1660 — the primary/secondary two-types-one-model fixture the secondary-emitter test mirrors with `model`-strategy defaults on both so the model-label-routing audit passes), `services.seed_data(N)` first-line seeding for db-touching tests (AGENTS.md catalog rule, `test_relay_node_field.py:88` precedent).
- **New helpers justified:** exactly one — `global_id_for(type_cls, id) -> str` in `django_strawberry_framework/testing/relay.py`. Single responsibility: gate (stamped-strategy present + string strategy) then delegate (payload via `encode_typename`, encoding via `relay.GlobalID`). It serves consumer test suites plus this build's own Slice-6 assertion-churn work (spec line 606 mints book ids with it). No second module-level helper is warranted: the function body is ~15 lines of gate + 3 lines of delegation.
- **Duplication risk avoided:**
  - Re-deriving the payload mapping locally (the staged pseudocode at `testing/relay.py:21-24` sketches exactly this `if strategy in {"model", "type+model"}` fork) — avoided by calling `encode_typename`; the staged pseudocode is a sketch, not the contract, and the plan supersedes it.
  - A `{"callable", "custom"}` literal — avoided via `strategy not in STRING_GLOBALID_STRATEGIES` (after the `None` gate), keeping types/relay.py's no-literal contract intact.
  - A decode wrapper — avoided by plain re-export + `__all__` listing.
  - A 4th hand-typed copy of the Relay-gate wording — avoided via `_RELAY_NODE_GATE_LEAD`.
  - Test-helper near-copies of `test_relay_node_field.py`'s `_make_node_type` / `_schema_with` / `_gid` — accepted as small file-local copies, the same per-file-self-contained pattern every prior package test module in this build uses; pre-cleared for Worker 3 as not-a-DRY-finding (cross-file test-helper consolidation, if ever, belongs to the integration pass — it is NOT added to the standing ledger because each copy is ≤10 lines and file-local readability wins).

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing.

1. **Rewrite `django_strawberry_framework/testing/relay.py` wholesale** (currently a docstring + two staged anchor blocks; both anchors removed). New contents, in order:
   - Module docstring: the public contract — what each helper does, the strategy table (`model` / `type+model` → model-label payload; `type` → `graphql_type_name` payload; `callable` / `custom` → raise), the finalize-first requirement, and the **asymmetry contract paragraph** (Decision 10 / Revision 2 P2): a secondary model-label emitter's `global_id_for` output decodes to the model's PRIMARY via `registry.get(model)` — round-trip identity holds only for lone/primary model-label types and `type`-strategy payloads, and this is exactly the routing a live `node(id:)` performs on the same id. Keep the existing "lives under `testing/` because the audience is consumer test suites" framing.
   - Imports (module top — safe: `types/relay.py` and `types/base.py` cycle-dodge their own heavy imports in-function and neither imports `testing/`): `from strawberry import relay`; `from django_strawberry_framework.exceptions import ConfigurationError`; `from django_strawberry_framework.types.base import STRING_GLOBALID_STRATEGIES, _RELAY_NODE_GATE_LEAD`; `from django_strawberry_framework.types.relay import decode_global_id, encode_typename`. The `decode_global_id` import IS the public re-export.
   - `__all__ = ["decode_global_id", "global_id_for"]` (alphabetical).
   - `def global_id_for(type_cls: type, id: object) -> str:` —
     a. `definition = getattr(type_cls, "__django_strawberry_definition__", None)`; `None` → `ConfigurationError` naming `global_id_for` and that the input is not a registered `DjangoType` subclass.
     b. `strategy = definition.effective_globalid_strategy` (the finalize-stamped read — never `_resolve_globalid_strategy`, never the setting). If `None`: when `not definition.finalized` → `ConfigurationError` with the finalize-first remediation (name `finalize_django_types()` / building the schema); else (finalized but never stamped ⇒ not Relay-Node-shaped) → `ConfigurationError` composing `_RELAY_NODE_GATE_LEAD` (the spec's "Non-finalized / non-Relay-Node inputs raise with the finalize-first remediation", split into the two precise causes the two spec-named tests pin).
     c. If `strategy not in STRING_GLOBALID_STRATEGIES` (i.e. the stamped classification is `callable` or `custom`) → `ConfigurationError` stating those encoders run on a live `(root, info)` pair the helper does not have, so it cannot promise the emitted payload (Decision 10 wording; mention the consumer-owns-its-helper line).
     d. `payload = encode_typename(definition, strategy, type_cls, None, None)` — with a short comment: string-strategy branches never touch `root` / `info`, and the `callable` branch is unreachable here (step c).
     e. `return str(relay.GlobalID(type_name=payload, node_id=str(id)))`.
2. **`django_strawberry_framework/testing/__init__.py` — docstring-only edit** (the staged anchor at line 34 prescribes it; remove the anchor in the same change): add `global_id_for` / `decode_global_id` to the module docstring's "Currently exports" section as a pointer at the dotted `django_strawberry_framework.testing.relay` submodule path. **NO re-export, NO `__all__` change** — Decision 10 / the card's DoD name the submodule path, and the export gate stays exactly as the spec writes it (the root-namespace export was a rejected alternative, Decision 10). The `TestClient` / `GraphQLTestCase` "Future exports (0.0.12)" note stays untouched. Side benefit worth a docstring half-sentence at Worker 2's discretion: `import django_strawberry_framework.testing` stays light — `testing/relay.py`'s `types.base` import is paid only by suites that import the submodule.
3. **Replace `tests/testing/test_relay.py`'s staged stub with the real suite** (anchor at line 9 removed) per `### Test additions / updates` below. Module docstring drops the "Staged test home" framing for a "Tests for the public `testing.relay` helpers (spec-032 Slice 5, Decision 10)" one; keep the `docs/TREE.md`-mirror note.
4. **Grep-verify** zero `TODO(spec-032 … Slice 5)` anchors remain anywhere; Slice 6 / Slice 7 anchors untouched.
5. `uv run ruff format .` and `uv run ruff check --fix .`; classify any churn per the build-report template. No pytest beyond the focused `--no-cov` runs Worker 2 elects.

No edits to `django_strawberry_framework/__init__.py` (Worker 3's public-surface check should confirm `git diff -- django_strawberry_framework/__init__.py` is empty — Decision 10 rejected the root export), none to `types/relay.py`, none to `CHANGELOG.md` (Slice 7's grant), none to `docs/TREE.md` (Slice 7 owns the tree update; the staged anchor there already lists both files).

### Test additions / updates

All in `tests/testing/test_relay.py` (new suite; mirrors `testing/relay.py` per `docs/TREE.md` — Decision 11, no card conflict). Spec Test plan lines 584-589, all eight spec-named tests enumerated; package-only placement is correct per the Test-plan family reasons: the helpers are consumer-test-suite utilities never reachable from a live `/graphql/` request (their live usage arrives in Slice 6's assertion churn), and the raise paths are type-creation/finalization states an example schema cannot carry. File-local fixtures: autouse `_isolate_registry` (`registry.clear()` bracket), a `_make_node_type`-style builder over `apps.products.models` (`Category` / `Item`), a minimal `_schema_with`-style query builder using `strawberry_config()`; db-touching tests are `@pytest.mark.django_db` with first-line `services.seed_data(1)` (AGENTS.md catalog rule); pure type-creation raise tests follow the no-seed `test_relay_interfaces.py` precedent.

- `test_global_id_for_model_strategy` — finalized default-strategy type; **cross-checked against a schema execution** (spec line 586): execute `{ … { id } }` through a real `strawberry.Schema` for a seeded row and assert the returned id string `== global_id_for(T, row.pk)`; additionally assert the decoded payload is the model label (`products.category:…` shape via `relay.GlobalID.from_id`).
- `test_global_id_for_type_strategy` — `globalid_strategy = "type"`; live id equals the helper output and the payload slot is the `graphql_type_name` (covers `Meta.name` honoring if the fixture sets `name=`, at Worker 2's discretion).
- `test_global_id_for_type_plus_model_strategy` — `globalid_strategy = "type+model"`; live id equals helper output; payload is the model label.
- `test_global_id_for_callable_or_custom_raises` — parametrized over the two classifications: a `Meta.globalid_strategy` callable (stamped `"callable"`) and a consumer `resolve_typename` override (stamped `"custom"`, the `test_relay_interfaces.py:1572` fixture shape); both finalize cleanly, then `global_id_for` raises `ConfigurationError` whose message names the live-`root`/`info` reason. No db.
- `test_global_id_for_unfinalized_raises` — a Relay-shaped type defined but `finalize_django_types()` NOT called; `ConfigurationError` with the finalize-first remediation (assert the remediation substring). No db.
- `test_global_id_for_non_node_raises` — a **finalized** non-Relay `DjangoType` (no `interfaces`); `ConfigurationError` composing the `_RELAY_NODE_GATE_LEAD` wording. Worker 2 may fold a plain-non-DjangoType input (e.g. `object`) into this test as a second case (step-1a branch); that extra case is in-contract coverage, not scope creep.
- `test_public_decode_round_trip_primary_and_type_name` — `decode_global_id(global_id_for(T, pk)) == (T, str(pk))` for (a) a lone `model`-strategy type and (b) a `type`-strategy type (spec line 588, Revision 2 P2); import `decode_global_id` **from `django_strawberry_framework.testing.relay`** (proving the re-export, not the internal path); an identity assertion `testing.relay.decode_global_id is types.relay.decode_global_id` is permitted as a one-line re-export pin.
- `test_secondary_model_label_emitter_decodes_to_primary` — two Relay types over `Item`, primary (`Meta.primary = True`) and secondary, both on the default `model` strategy (the audit passes: the primary accepts model-label decode); `global_id_for(SecondaryType, pk)` mints the same model-label payload the secondary's live closure emits (cross-check via the installed `resolve_typename` or a schema execution, Worker 2's choice), and `decode_global_id(...)` returns `(PrimaryType, str(pk))` — the documented asymmetry (spec line 589).

Count: 8 test functions (~9 cases with the callable/custom parametrization — matches the impl-table estimate). Temp/scratch tests: none needed; the suite is small and self-contained. Worker 3 focused run: `uv run pytest tests/testing/ --no-cov` (and `tests/types/test_relay_interfaces.py` if touching suspicion arises — this slice must not change its behavior).

### Implementation discretion items

Assessed and decided as Worker 2's choice (style-level only; the architecture above is fixed):

- Exact `ConfigurationError` message wording for the four raise branches, provided each names `global_id_for`, the non-Node branch composes `_RELAY_NODE_GATE_LEAD`, the unfinalized branch names the finalize-first remediation, and the callable/custom branch states the live-`(root, info)` reason. No message needs (or should get) a `GraphQLError` code — these are test-time configuration errors, not request-boundary errors.
- Keyword vs positional construction of `relay.GlobalID(type_name=…, node_id=…)` (the shipped `_gid` test helper uses positional; both verified working).
- Whether the callable/custom test uses `@pytest.mark.parametrize` over fixture-builder callables or two plain test bodies under one name is Worker 2's call — keep the single spec-named test function name either way.
- The cross-check mechanism for the secondary-emitter mint (direct `resolve_typename` invocation via a `test_relay_interfaces.py::_emitted_typename`-style fake root vs a full schema execution).
- Fixture-helper naming and whether `_make_node_type` accepts a `primary=` kwarg vs a separate two-type builder.

### Spec slice checklist (verbatim)

- [x] New [`django_strawberry_framework/testing/relay.py`][testing-init]: `global_id_for(type_cls, id)` — the strategy-aware encoded `GlobalID` string a finalized Relay-Node-shaped type emits for a pk (`model` / `type+model` → model-label payload; `type` → `graphql_type_name` payload; `callable` / `custom` → [`ConfigurationError`][glossary-configurationerror], encode needs a live `root` / `info`) — and `decode_global_id(gid)` — the public re-export of the internal dispatch returning `(target_type, node_id)`. The pair is asymmetric for a secondary model-label emitter: `global_id_for` mints the payload the secondary emits, and decode routes it to the model's **primary** — round-trip identity holds only for lone/primary model-label types and `type`-strategy payloads ([Decision 10](#decision-10--public-testingrelaypy-helpers-and-the-export-gate), Revision 2 P2).
- [x] Package coverage: `tests/testing/test_relay.py` (new — mirrors `testing/relay.py` per [`docs/TREE.md`][tree]).

### Notes for Worker 1 (spec reconciliation)

None at planning. Every symbol the spec names for this slice exists on disk and was verified: `effective_globalid_strategy` stamping (`types/relay.py::install_globalid_typename_resolver` step 3), `decode_global_id` (`types/relay.py:596`), `encode_typename` (`types/relay.py:415`), the staged `testing/relay.py` / `testing/__init__.py` / `tests/testing/test_relay.py` homes, and `registry.get(model)` primary routing inside decode. The spec's "Non-finalized / non-Relay-Node inputs raise with the finalize-first remediation" (Decision 10) is implemented as two discriminated messages (finalize-first vs Relay-gate) because the two spec-named tests pin the two causes separately — an in-plan reading, not a spec gap.

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/testing/relay.py` — wholesale rewrite of the staged stub (both Slice-5 anchors removed): module docstring carrying the public contract (strategy table, finalize-first requirement, the Decision-10/Revision-2-P2 asymmetry paragraph, the keep-`testing/__init__`-light note), module-top imports (cycle-safe per the plan), `__all__ = ["decode_global_id", "global_id_for"]` (the `decode_global_id` import IS the re-export — no wrapper), and `global_id_for(type_cls, id)` implementing the plan's steps a–e verbatim: definition gate → stamped-strategy read with the two discriminated `None` raises (unfinalized vs finalized-non-Node via `_RELAY_NODE_GATE_LEAD`) → `strategy not in STRING_GLOBALID_STRATEGIES` rejection (no `{"callable", "custom"}` literal introduced) → `encode_typename(definition, strategy, type_cls, None, None)` → `str(relay.GlobalID(type_name=payload, node_id=str(id)))`.
- `django_strawberry_framework/testing/__init__.py` — docstring-only edit per the staged anchor's prescription (anchor removed in the same change): `global_id_for` / `decode_global_id` added to "Currently exports" as a pointer at the dotted `django_strawberry_framework.testing.relay` submodule path, including the import-stays-light half-sentence the plan offered at discretion. NO re-export, NO `__all__` change; the `TestClient` / `GraphQLTestCase` "Future exports (0.0.12)" note untouched.
- `tests/testing/test_relay.py` — staged stub replaced with the real 8-test suite (anchor removed); docstring re-framed per plan step 3, `docs/TREE.md`-mirror note kept.
- `django_strawberry_framework/__init__.py` — NOT touched by this pass (its dirty state in `git status` is the prior slices' uncommitted diff; Worker 3's `git diff` check should compare against the pre-build baseline, not HEAD-clean).

### Tests added or updated

All new, in `tests/testing/test_relay.py` (8 functions / 9 cases — matches the impl-table estimate):

- `test_global_id_for_model_strategy` — helper output `==` the live `{ row { id } }` schema-executed id for a seeded `Category` row; decoded payload asserted as `products.category` + `str(pk)`.
- `test_global_id_for_type_strategy` — live id equals helper output under `globalid_strategy = "type"`; payload slot is the honored `Meta.name` (`CategoryNode`).
- `test_global_id_for_type_plus_model_strategy` — live id equals helper output; payload is the model label.
- `test_global_id_for_callable_or_custom_raises` — parametrized (`callable` via a 4-positional `Meta.globalid_strategy` encoder, `custom` via a consumer `resolve_typename` override); both finalize cleanly with the expected stamped classification, then raise naming `global_id_for`, the `(root, info)` reason, and the classification. No db.
- `test_global_id_for_unfinalized_raises` — Relay-shaped type, no finalize; message names the type and `finalize_django_types()`. No db.
- `test_global_id_for_non_node_raises` — finalized non-Relay `DjangoType` raises the `_RELAY_NODE_GATE_LEAD` wording (substring assert, no regex); second case folds in the plan-permitted plain-`object` input → "not a registered DjangoType subclass". No db.
- `test_public_decode_round_trip_primary_and_type_name` — `decode_global_id(global_id_for(T, 7)) == (T, "7")` for a lone `model`-strategy type and a `type`-strategy type; `decode_global_id` imported from `django_strawberry_framework.testing.relay`, plus the one-line `testing.relay.decode_global_id is types.relay.decode_global_id` re-export pin.
- `test_secondary_model_label_emitter_decodes_to_primary` — primary + secondary over `Item`, both default `model` strategy; minted payload is `products.item`, cross-checked against the secondary's installed live closure via a file-local `_emitted_typename` fake-root helper, and `decode_global_id` returns `(PrimaryItem, "3")`.

### Validation run

- `uv run ruff format .` — pass (241 files left unchanged; my files were written format-clean).
- `uv run ruff check --fix .` — pass ("All checks passed!", zero fixes applied).
- `git status --short` after both — modified: `testing/relay.py`, `testing/__init__.py`, `tests/testing/test_relay.py` (all three slice-intended, listed above). Every other entry (`django_strawberry_framework/__init__.py`, `connection.py`, `registry.py`, `relay.py`, `types/{base,definition,finalizer}.py`, the `tests/` siblings, `examples/fakeshop/test_query/test_library_api.py`, the spec, the deleted 031 `bld-*` artifacts, the untracked 032 `bld-*` artifacts) is the prior Slices-1–4 / build-cycle uncommitted state, dirty before this pass started and byte-untouched by it (ruff reported zero reformats/fixes, so no tool churn either). Nothing reverted.
- Focused tests (`--no-cov`): `uv run pytest tests/testing/test_relay.py tests/types/test_relay_interfaces.py --no-cov` — **124 passed** (9 new cases + 115 untouched `test_relay_interfaces` siblings, confirming this slice changed none of their behavior); `uv run pytest tests/testing/ --no-cov` — **15 passed** (the 6 `test_wrap.py` neighbors green after the `__init__` docstring edit).
- Anchor grep: `grep -rn "TODO(spec-032" … | grep "Slice 5"` — zero hits; total remaining `TODO(spec-032` anchors = 6 (the 3 Slice-6 + 3 Slice-7 sites the plan lists), untouched.

### Implementation notes

- Raise-message wording (the plan's discretion item): all four name `global_id_for:` as the prefix; the unfinalized branch says "call finalize_django_types() (or build the schema) first - the GlobalID strategy is stamped at finalization"; the non-Node branch composes `_RELAY_NODE_GATE_LEAD` with the connection/globalid gates' "or inherit `relay.Node` directly." tail (the 4th byte-identical recomposition, matching `types/base.py:322`'s shape rather than relation_shapes' "or remove the key."); the callable/custom branch includes `{strategy!r}` so the test can pin the stamped classification, plus the Decision-10 "consumer with a custom encoder owns its own test helper" line.
- `relay.GlobalID(type_name=…, node_id=…)` constructed with keywords (the discretion item; reads better at the single call site than the `_gid` helper's positional form).
- `id` parameter kept as the spec-named `id` with `# noqa: A002` (the Slice-2 resolver precedent for spec-pinned builtin-shadowing names).
- Schema cross-check fixture: a `_schema_with_row(node_type, model)` builder exposing one `row` field via `strawberry.field(resolver=…)` whose return annotation is the closure-captured node type — finalizes inside the builder like `test_relay_node_field.py::_schema_with`, but needs no `extra_types` (the concrete type is reachable through the field). Query is the constant `{ row { id } }`.
- Callable/custom parametrization (the discretion item): `@pytest.mark.parametrize` over two module-level builder callables with `ids=["callable", "custom"]`, keeping the single spec-named function name.
- Secondary-emitter cross-check (the discretion item): direct `resolve_typename` invocation via a file-local `_emitted_typename` fake-root copy of the `test_relay_interfaces.py` helper (no schema execution needed — the three strategy tests already pin live-schema parity).
- `_make_node_type` grew `interfaces=` / `primary=` kwargs (one builder serves Node, non-Node, and the primary/secondary pair — the plan's "primary= kwarg vs separate builder" discretion resolved toward one builder).
- Import sort: ruff's isort places `_RELAY_NODE_GATE_LEAD` before `STRING_GLOBALID_STRATEGIES` (underscore sorts first); written that way so format is a no-op.

### Notes for Worker 3

- Per the plan, run `scripts/review_inspect.py` on the now-real `django_strawberry_framework/testing/relay.py` (it was statement-free at planning) with `--output-dir docs/shadow`.
- No shadow files were used for this pass; the plan's own line-pinned readings of `types/relay.py` / `types/base.py` were re-verified against current source before editing (all pins still accurate).
- Public-surface check: `django_strawberry_framework/__init__.py` shows modified in `git status` but that diff is prior slices' work — verify this pass added nothing to it (no `global_id_for` / root export) rather than expecting an empty status line.
- The file-local `_make_node_type` / `_schema_with_row` / `_emitted_typename` near-copies of other test modules' helpers are pre-cleared by the plan's DRY analysis as not-a-DRY-finding (≤10-line file-local copies, the per-file-self-contained pattern).

### Notes for Worker 1 (spec reconciliation)

None. The plan was implemented without drift: no new helpers beyond `global_id_for`, no payload re-derivation, no `{"callable", "custom"}` literal, the two discriminated `None`-stamp raises land exactly as the plan's in-plan reading described, and the package root export gate is untouched.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **No payload re-derivation** — verified: `global_id_for` delegates the payload to `types/relay.py::encode_typename` (`testing/relay.py::global_id_for #"payload = encode_typename"`), the same function the live `_install_typename_closure` closure calls. No local `label_lower` / `graphql_type_name` fork; the staged pseudocode's `if strategy in {"model", "type+model"}` sketch was correctly superseded.
- **No `{"callable", "custom"}` literal** — verified by grep: the rejection is `strategy not in STRING_GLOBALID_STRATEGIES` (imported from `types/base.py:104`), preserving types/relay.py's absence-from-both-memberships contract. Zero new copies of the strategy-set literals anywhere in the diff.
- **Gate-lead recomposition byte-consistent** — probe-verified programmatically: the non-Node raise composes `f"... {_RELAY_NODE_GATE_LEAD} " "or inherit `relay.Node` directly."`, character-identical to the `types/base.py:322` shape (the 4th recomposition site, matching the Slice-3 precedent; the `_validate_connection` / `_validate_relation_shapes` sites use their own spec-pinned tails and were not disturbed).
- **Bare re-export, no wrapper** — `decode_global_id` is the imported name itself (`__all__` lists it); the test pins identity (`testing.relay.decode_global_id is types.relay.decode_global_id`). No duplicated docstring contract.
- **Observed but accepted: 4x `"global_id_for: "` message prefix** (review_inspect "Repeated string literals", `testing/relay.py::global_id_for`, the four raise branches). Accepted with reason: the plan's discretion item mandates each message name `global_id_for`, all four sites live inside one ~40-line function, and a hoisted prefix constant would hurt readability for a 15-character fragment. Noted for the integration-pass repeated-literals comparison only; no action required.
- **File-local test-helper near-copies** (`_make_node_type` / `_schema_with_row` / `_emitted_typename` vs `tests/test_relay_node_field.py` / `tests/types/test_relay_interfaces.py` shapes) — pre-cleared by the plan's DRY analysis as the established per-file-self-contained pattern (≤10-line copies); not a finding, consistent with every prior package test module this build accepted.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows exactly the Slice-2 change set: the `from .relay import DjangoNodeField, DjangoNodesField` import + the two `__all__` entries + the removed Slice-2 anchor (spec-authorized at the Slice-2 checklist, "exported from `django_strawberry_framework/__init__.py` (the card's DoD names both)" — spec line 93; accepted at Slice 2's review). **No NEW change from Slice 5**: no `global_id_for` / `decode_global_id` / `testing` import appears — the Decision-10 rejected-alternative (root export) stayed rejected. `testing/__init__.py`'s diff is docstring-only (anchor removed, "Currently exports" pointer added at the dotted submodule path); `__all__ = ["safe_wrap_connection_method"]` is byte-unchanged and there is no re-export. Export gate intact.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. (The `testing/__init__.py` and `testing/relay.py` docstring updates are source docstrings, reviewed above; Slice 7 owns `docs/TREE.md` / `docs/README.md` / GLOSSARY, whose Slice-7 anchors are confirmed untouched.)

### What looks solid

- **The stamped-strategy read (Revision 7 P3) is exact**: `definition.effective_globalid_strategy` only — never `_resolve_globalid_strategy`, never the setting — making the helper consistent-by-construction with live emission; the `None` stamp doubles as the finalized-Relay-Node gate and the `definition.finalized` check cleanly discriminates the two causes (slot defaults verified at `types/definition.py:146-147`).
- **The asymmetry contract (Revision 2 P2) is pinned in code, docstring, and tests**: the module docstring carries the full paragraph; `test_secondary_model_label_emitter_decodes_to_primary` asserts all three legs (minted payload == `products.item`, == the secondary's installed live closure output via `_emitted_typename`, decode routes to `(PrimaryItem, "3")`); `test_public_decode_round_trip_primary_and_type_name` restricts identity to exactly the lone-model-label and `type`-strategy shapes.
- **All eight spec-named tests landed** (9 cases with the callable/custom parametrization), each matching the Test-plan line 584-589 description; the three strategy tests cross-check against a real `strawberry.Schema` execution per spec line 586, with first-line `services.seed_data(1)` on every db-touching test (AGENTS.md catalog rule) and no-db raise tests per the `test_relay_interfaces.py` precedent.
- **The `encode_typename(definition, strategy, type_cls, None, None)` call is safe by construction**: read against `types/relay.py::encode_typename` — the `model`/`type+model` branch reads `definition.model._meta.label_lower`, the `type` branch reads `definition.graphql_type_name`, and only the `callable` branch touches `root`/`info`, which the `STRING_GLOBALID_STRATEGIES` gate makes unreachable. The in-code comment states exactly this.
- **Anchor discipline**: zero `TODO(spec-032 … Slice 5)` anchors remain (grep-verified); the 6 Slice-6/7 anchors are untouched; no "staged" wording survives in either rewritten module docstring (the Slice-4 lesson applied).
- Focused runs green: `tests/testing/test_relay.py` 9 passed alone; `tests/testing/ + tests/types/test_relay_interfaces.py` 130 passed (`--no-cov`) — the interfaces siblings unchanged in behavior. `ruff format --check` / `ruff check` clean on the three slice files (read-only invocations).

### Temp test verification

- Temp test files used: none. The shipped suite plus two read-only probes (the gate-lead byte-consistency check and the focused pytest runs) covered every review suspicion; no behavior gap warranted a `docs/builder/temp-tests/slice-5/` probe.
- Disposition: nothing to promote or delete.
- Static helper: `scripts/review_inspect.py django_strawberry_framework/testing/relay.py --output-dir docs/shadow` RUN (mandated — new `.py` file with logic; the plan pinned this for Worker 3). Output walked in full: 4 imports (all justified, cycle-safe per the plan), 1 symbol, 1 hotspot (`global_id_for`, 42 lines / 4 branches — a linear gate chain, no complexity concern), zero Django/ORM marker lines, 1 `getattr()` (the definition gate, justified), zero TODOs, and the 1 repeated literal dispositioned under DRY findings above. Skips recorded: `django_strawberry_framework/testing/__init__.py` (docstring-only edit, no review-worthy logic) and `tests/testing/test_relay.py` (test file outside the mandatory triggers at 248 changed lines of test fixtures/assertions; its DRY surface was read directly).

### Spec slice checklist walk

Both verbatim boxes are ticked `- [x]` and both contracts verifiably landed in the diff (helper + re-export + asymmetry in `testing/relay.py`; the mirroring `tests/testing/test_relay.py` suite). No over-tick, no silent omission.

### Notes for Worker 1 (spec reconciliation)

Nothing requiring a spec edit. For the integration-pass ledger only: the `4x "global_id_for: "` message-prefix repetition (accepted, reasoned above) and the standing deferred items from Slices 1-4 are unchanged by this slice.

### Review outcome

`review-accepted` — zero High/Medium/Low findings; both DRY observations carry recorded accepted dispositions; the export gate, the stamped-strategy read, the asymmetry contract, and all eight spec-named tests are verified against Decision 10 / Revision 2 P2 / Revision 7 P3. Top-level `Status:` updated to `review-accepted`.

---

## Final verification (Worker 1)

- **Spec slice checklist audit (2 boxes):** both `- [x]` ticks verified against the diff. Box 1 (helpers + re-export + asymmetry): `django_strawberry_framework/testing/relay.py` ships `global_id_for` exactly per Decision 10 — definition gate, finalize-stamped `effective_globalid_strategy` read (never the setting), `STRING_GLOBALID_STRATEGIES` membership (no `{"callable", "custom"}` literal), payload via `encode_typename(definition, strategy, type_cls, None, None)`, encoding via `str(relay.GlobalID(...))` — and `decode_global_id` as a bare re-export (`__all__` lists it; the test pins `testing.relay.decode_global_id is types.relay.decode_global_id`); the asymmetry contract is in the module docstring and pinned by `test_secondary_model_label_emitter_decodes_to_primary`. Box 2 (package coverage): `tests/testing/test_relay.py` ships all eight spec-named tests (9 cases), mirroring `testing/relay.py` per `docs/TREE.md`. No over-tick, no deferral.
- **DRY check across Slices 1–5:** no payload re-derivation (delegates to `encode_typename`), no strategy-set literal fork, no decode wrapper — verified by reading the diff and grep. Two rulings:
  - **The 4x `"global_id_for: "` message prefix (Worker 3's observation): ACCEPTED as-is.** All four sites live inside one ~40-line function; each message must name the helper per the plan's discretion mandate; hoisting a 15-character prefix into a module constant would add indirection with zero consolidation value (no second module would ever import it). Stays on the integration-pass repeated-literals comparison list as a watch item only — no action.
  - **Gate-tail escalation for the integration ledger:** the byte-identical tail `"or inherit \`relay.Node\` directly."` is now at its **3rd** composed site (`types/base.py::_validate_connection`, `types/base.py` globalid gate at the `#"{subject} {_RELAY_NODE_GATE_LEAD}"` site, `testing/relay.py::global_id_for`), plus 2 parenthesized variants (`connection.py`, `relay.py`). The standing ledger recorded it at 2x after Slice 3; per the build's hoist-at-the-3rd-copy pattern this is now a priority consolidation candidate for the integration pass (e.g. fold the tail into `_RELAY_NODE_GATE_LEAD` or a composed-message helper). Not blocking this slice: the recomposition is probe-verified byte-consistent, and cross-slice hoists are the integration pass's designated work.
  - All other standing watch items (relation-resolver delegation, `.Meta.interfaces entry ` prefix, fifth-guard wording, unhoisted GraphQL doc literals, opted/bare description asymmetry, the stale "staged" docstring Low at `tests/test_relay_node_field.py`) carry to integration unchanged; Slice 5 added nothing to them.
- **Focused tests:** `uv run pytest tests/testing/ tests/types/test_relay_interfaces.py tests/test_relay_node_field.py --no-cov` — **156 passed** (no `--cov*` flags). The `test_relay_interfaces` / `test_relay_node_field` siblings are behaviorally untouched by this slice.
- **Anchor discipline:** grep confirms zero `TODO(spec-032 … Slice 5)` anchors remain; the 3 Slice-6 source anchors (and the Slice-7 doc anchors) are untouched.
- **Export gate:** re-verified — `testing/__init__.py` `__all__` is byte-unchanged (`["safe_wrap_connection_method"]`, docstring-only edit); no Slice-5 change to `django_strawberry_framework/__init__.py` (its diff is the accepted Slice-2 export set).
- **Spec reconciliation:** the plan's one in-plan reading (Decision 10's single "finalize-first remediation" clause implemented as two discriminated raises) was judged worth a clarifying spec edit rather than leaving the spec lumping two causes under one remediation — the shipped non-Node message carries the Relay-gate remediation, not the finalize-first one, and the contract record should match what ships. Edit made (below); `check_spec_glossary.py` re-run clean (38 terms OK).
- **Final status: `final-accepted`.**

### Summary

Slice 5 shipped the Decision-10 public test-helper surface: `django_strawberry_framework/testing/relay.py` with `global_id_for(type_cls, id)` (gate + delegate over the finalize-stamped strategy and `encode_typename`; four discriminated `ConfigurationError` branches) and `decode_global_id` as a bare re-export of the internal dispatch; a docstring-only pointer in `testing/__init__.py` with the export gate intact (no re-export, no root export); and the 8-test / 9-case `tests/testing/test_relay.py` suite pinning live-emission parity for all three string strategies, the four raise branches, the restricted round-trip identity, and the secondary-emitter decode asymmetry. Zero review findings; one new accepted repeated-literal disposition; one gate-tail ledger escalation for the integration pass.

### Spec changes made (Worker 1 only)

- `docs/spec-032-full_relay-0_0_9.md` line 5 (status line) — updated to "Slices 1–5 implemented … Slices 6–7 not started" with a one-clause Slice-5 note (Decision 10, export gate intact). Trigger: Slice 5 final acceptance; per-spawn status-line re-verification.
- `docs/spec-032-full_relay-0_0_9.md` Decision 10, `global_id_for` bullet (line 447) — the single sentence "Non-finalized / non-Relay-Node inputs raise with the finalize-first remediation." expanded to record the cause-discriminated remediations (unfinalized → finalize-first; finalized non-Relay-Node → add-`relay.Node` Relay-gate), matching the shipped implementation and the two spec-named tests that pin the causes separately. Trigger: Slice 5's recorded in-plan reading, promoted to spec text so the contract record matches what ships. `scripts/check_spec_glossary.py` re-run after both edits: exit 0, 38 terms OK.
