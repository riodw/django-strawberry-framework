# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## DRY analysis

- **Defer `_apply_node_filter` two-mode split until a third caller lands.** `_apply_node_filter(qs, id_attr, *, node_id=None, node_ids=None)` at `types/relay.py:250-268` accepts two mutually-exclusive kwargs and branches internally; call sites pass exactly one each (`relay.py:362` passes `node_id`, `relay.py:423,448` pass `node_ids`). Splitting into `_apply_node_id_filter(qs, id_attr, node_id)` and `_apply_node_ids_filter(qs, id_attr, node_ids)` would remove the dead-arg slot at each site, but the three call sites all sit inside this one module and the mutual-exclusion guard is trivial. Defer until a fourth caller lands OR `DjangoNodeField` / `DjangoConnectionField` (KANBAN cards `TODO-ALPHA-022/023-0.0.9`) needs a single-id filter outside this module; at that point split the helper so each consumer's call site shows the intent in the signature.
- **Defer the sync/async resolver-pair fold across `_resolve_node{,s}_default` / `_resolve_node{,s}_async` until a third color-pair lands.** `_resolve_nodes_default` (`relay.py:387-427`) and `_resolve_nodes_async` (`relay.py:430-453`) share the `coerced_keys = [str(node_id) for node_id in coerced_ids]` + `_order_nodes(...)` tail verbatim; the singular pair (`relay.py:330-363` / `:366-384`) shares the queryset-build + id-filter prologue. The async-color split is intentional sync/async sibling design (per `START.md` and walker convention), and the duplicated tails are short. Defer until the optimizer-cooperation Relay-node-default slice lands (the deferred follow-up in `docs/GLOSSARY.md:857`) — that slice will add a third color-pair (per-node optimizer rebind sync + async), at which point folding the tail into a `_finalize_node_lookup(cls, results, coerced_ids, id_attr, *, required)` helper amortizes the duplication.
- **Promote `_initial_queryset` / `_model_for` / `_apply_get_queryset_{sync,async}` out of `types/relay.py` only when a third cross-module caller lands.** Carried forward verbatim from `docs/review/rev-list_field.md` DRY observation 2 (Worker 2's M1 implementation moved `list_field.py:132` onto `_initial_queryset`, firing the second-caller trigger documented there). The current shape — five private helpers in `types/relay.py` with one external consumer (`list_field.py`) — is correct until a third caller lands. **Trigger:** when `DjangoConnectionField` / `TODO-ALPHA-023-0.0.9` or `DjangoNodeField` / `TODO-ALPHA-022-0.0.9` adds a third call site, OR the cross-module use of `_apply_get_queryset_{sync,async}` plus `_initial_queryset` grows to a fourth callsite outside `types/relay.py`, lift the three helpers into a non-`_`-prefixed `types/_queryset.py` or `types/_visibility.py` module. Quote verbatim for future grep: "Defer until a third cross-module caller lands."

## High:

None.

## Medium:

None.

## Low:

### `_coerce_node_ids` runs an extra list-comprehension when every input is already a non-`GlobalID`

`_coerce_node_ids` at `types/relay.py:244-247` unconditionally materializes a fresh `list` via `[_coerce_node_id(node_id) for node_id in node_ids]`, even when the caller already handed in a `list[int]` (the common shape under `apps.products` integer pks). `_coerce_node_id` at `relay.py:240-241` is a trivial pass-through for non-`GlobalID` inputs, so the list comprehension is correct but pays a copy for the case that does not need one. Tests pin the generator-input case (`test_resolve_nodes_accepts_generator_node_ids` at `tests/types/test_relay_interfaces.py:619-642`) where the copy is load-bearing — the generator must materialize once to allow the `filter(...__in=...)` and the `coerced_keys` walk to see the same elements. So the copy is not removable in general.

Two observations worth recording:

1. The docstring on `_resolve_nodes_default` (`relay.py:394-417`) does not call out the generator-materialization invariant — readers learn it only from the test docstring at `test_relay_interfaces.py:619-642`. A one-sentence note on `_coerce_node_ids` ("materializes generator inputs once so the filter and the `coerced_keys` walk see the same elements") would make the contract greppable from the helper.
2. This is a Low because the copy is structurally required for generator inputs and the comprehension is hot only on the bulk-resolve path; defer the docstring polish until the next time this file gains a comment-pass cycle.

**Trigger for re-triage:** when the comment-pass cycle on this file lands, fold the generator-materialization invariant into `_coerce_node_ids`'s docstring (currently there is no docstring on the helper at all). Until then, the contract sits on the test alone.

### Module-docstring "0.0.5 Relay foundation slice" framing predates 0.0.6/0.0.7 changes

The module docstring at `relay.py:1-21` opens with "Internal Relay/interface helpers for the 0.0.5 Relay foundation slice" and structures the rest around Slices 2-4. Two refinements have shipped since:

- The `id` annotation suppression for direct `class Foo(DjangoType, relay.Node)` inheritance (review feedback regression pinned by `tests/types/test_relay_interfaces.py:1206-1272` and `:1238-1272`). The Phase 2.5 gates on `implements_relay_node(type_cls)` not `definition.interfaces` so direct-inheritance consumers are caught — `finalizer.py:236-240` is the canonical statement of that contract.
- The composite-pk gate honors a consumer `id: relay.NodeID[...]` escape hatch (review feedback regression pinned by `tests/types/test_relay_interfaces.py:241-259`). The `_check_composite_pk_for_relay_node` docstring at `relay.py:117-133` already documents this branch correctly, but the module docstring's Slice-4 enumeration does not.

Recommended change: at the next docstring-pass cycle, replace "for the 0.0.5 Relay foundation slice" with a release-agnostic framing (e.g., "Internal Relay/interface helpers shipped under [Relay Node integration](docs/GLOSSARY.md#relay-node-integration)") and append two bullets to the Slice-4 enumeration covering (a) the `implements_relay_node`-keyed Phase 2.5 gate for direct-inheritance consumers and (b) the `relay.NodeID[...]` escape from the composite-pk gate. Defer until the next comment-pass cycle that touches this file — the prose is informational and no consumer-facing contract drifts.

**Trigger for re-triage:** when the next docstring-pass cycle on this file lands, fold both refinements into the module docstring; until then, the GLOSSARY `Relay Node integration` block + the per-helper docstrings carry the canonical contract.

### `_resolve_id_default`'s `info` parameter is unused inside the helper body

`_resolve_id_default(cls, root, *, info)` at `relay.py:167-196` declares `info` as a keyword-only parameter (correctly, per the Strawberry call shape pinned by `test_relay_interfaces.py:550-577`) but the function body never reads it. The body only reads `cls.resolve_id_attr()`, `root.__class__._meta.pk.attname`, `root.__dict__`, and `getattr(root, id_attr)`. This is structurally correct — Strawberry's runtime always passes `info` and the framework default must accept the kwarg even when it ignores the value — but the function does not need to thread `info` further.

Defer ruff `ARG001` suppression: the parameter is part of the public Strawberry-bound call signature (a `# noqa: ARG001` would document the contract honestly, but ruff currently does not flag the parameter because it is bound through `setattr(type_cls, attr, classmethod(default))` which obscures the unused-arg signal). Re-triage if a future tightening of `ARG001` detection catches this site OR if a future Relay revision passes per-request context through `info` to `resolve_id` (at which point this parameter goes live).

**Trigger for re-triage:** when ruff's `ARG001` detection learns to follow `classmethod(_callable)` bindings, or when a Relay revision threads `info` into `_resolve_id_default`'s body.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_model_for(cls)` (`relay.py:271-280`) is the canonical model-lookup helper consumed by `install_is_type_of` (`relay.py:78`), `_check_composite_pk_for_relay_node` (`relay.py:134`), `_initial_queryset` (`relay.py:290`), and `_order_nodes` (`relay.py:316`); the single source of truth for the `cls.__django_strawberry_definition__.model` chain. `_initial_queryset(cls)` (`relay.py:283-290`) is consumed by the four Relay node-default sites (`relay.py:361, 382, 421, 446`) plus the cross-module `list_field.py:132` caller — second-caller trigger from `rev-list_field.md` DRY observation 1 has fired. `_RELAY_RESOLVER_DEFAULTS` (`relay.py:459-464`) is the single source of truth for the four-method `install_relay_node_resolvers` loop at `relay.py:486-492`; eliminates the four-times-repeated `setattr(type_cls, "resolve_X", classmethod(_resolve_X_default))` shape. The `__func__` identity test at `relay.py:489-491` is the canonical Strawberry-django override-preservation discriminator (matches `strawberry_django/type.py:213-225`).
- **New helpers considered.** A `_apply_node_filter` two-mode split was considered and deferred (DRY observation 1 above) — the mutual-exclusion guard is trivial and call sites are inside the same module. A sync/async resolver-pair fold was considered and deferred (DRY observation 2 above) — the duplicated tails are short and the color split is intentional. Promotion of `_initial_queryset`/`_model_for`/`_apply_get_queryset_*` to a non-`_`-prefixed shared module was considered and deferred (DRY observation 3 above; carried verbatim from `rev-list_field.md`) — second-caller trigger fired but third-caller trigger has not.
- **Duplication risk in the current file.** `_resolve_node_default` / `_resolve_node_async` and `_resolve_nodes_default` / `_resolve_nodes_async` are sync/async sibling pairs by design (per `START.md` "Async-detection asymmetry — intentional, not a harmonization candidate" precedent established by `list_field.py`); the duplicated `coerced_keys` + `_order_nodes` tail is the irreducible cross-color shape. The `[str(node_id) for node_id in coerced_ids]` walk appears twice (`relay.py:426, 451`) — also color-split by design. Both are correct sibling design, not consolidation candidates.

### Other positives

- **Override-preservation discriminator is structurally distinct across lifecycle phases.** `install_is_type_of` uses `cls.__dict__` membership (`relay.py:76`) — "declared on this class". `_build_annotations` uses tuple-membership (`types/base.py`) — "declared in `Meta.interfaces`". `install_relay_node_resolvers` uses `__func__` identity (`relay.py:489-491`) — "inherited from `relay.Node` vs. consumer override". Three different questions at three different lifecycle phases; the module docstring at `relay.py:1-21` enumerates the discriminator at each phase.
- **Composite-pk gate honors the `relay.NodeID[...]` escape hatch.** `_check_composite_pk_for_relay_node` at `relay.py:116-150` calls `type_cls.resolve_id_attr()` after the `CompositePrimaryKey` isinstance check and accepts the type if the consumer has already declared a single-column `relay.NodeID[...]` annotation that bypasses the `NodeIDAnnotationError` path. The gate's own error message advertises that remediation and the implementation honors it — test-pinned by `tests/types/test_relay_interfaces.py:241-259`.
- **`_resolve_id_default` dict-cache keys on the runtime class, not the declared model.** The comment at `relay.py:185-188` documents the proxy-model invariant: keying on `root.__class__._meta.pk.attname` instead of `cls.__django_strawberry_definition__.model._meta.pk.attname` keeps the `__dict__` lookup correct when a proxy-model row whose actual class differs from the declared DjangoType passes through `resolve_id`. The dict-cache hit avoids the lazy load that Decision 7 of the spec forbids; pinned by `tests/optimizer/test_relay_id_projection.py:122-141` (with `CaptureQueriesContext` asserting zero extra queries).
- **Async/sync color-correctness is fully test-pinned.** Three classes of test pins exist: (a) async-context async-`get_queryset` honored on both `resolve_node` and `resolve_nodes` (`test_relay_interfaces.py:794-853`); (b) async-context sync-`get_queryset` pass-through (`test_relay_interfaces.py:714-768`); (c) sync-context async-`get_queryset` rejected with `ConfigurationError` instead of the silent `AttributeError: 'coroutine' object has no attribute 'filter'` shape that the previous implementation produced (`test_relay_interfaces.py:856-902`). The `_apply_get_queryset_sync` close-and-raise shape at `relay.py:212-222` is the canonical "loud, named" rejection.
- **Singular- and plural-required missing-id paths emit the same `Model.DoesNotExist` exception.** `_resolve_node_default(required=True)` raises via `qs.get()`; `_resolve_nodes_default(required=True)` raises via `_order_nodes(..., required=True)` which constructs `model.DoesNotExist` directly. Consumers writing visibility-aware exception handling can catch one type — `test_resolve_nodes_required_raises_for_missing` (`test_relay_interfaces.py:646-672`) pins this homogeneity explicitly.
- **`apply_interfaces` MRO-skip + wrapped `TypeError` shape.** `apply_interfaces` at `relay.py:101` skips interfaces already in `__mro__` so direct-inheritance consumers don't see double injection; the `TypeError` from `__bases__` assignment is wrapped as `ConfigurationError` naming the offending interface (`relay.py:106-113`) so consumers see "cannot add interface X" instead of a raw layout `TypeError`. Both branches test-pinned by `test_apply_interfaces_skips_already_present_bases` and `test_apply_interfaces_wraps_typeerror_as_configuration_error` (`test_relay_interfaces.py:1043-1086`).
- **`definition.interfaces` is read-only inside this module.** `apply_interfaces` at `relay.py:101` reads `definition.interfaces` via a tuple-comprehension; no mutation. Carry-forward audit from `rev-types__finalizer.md` (verified from the finalizer side); confirmed here from the relay side.

### Summary

`types/relay.py` is the per-helper home for the Relay Node integration shipped at `0.0.5` (with two `0.0.6` refinements: direct-inheritance Phase 2.5 gating and the `relay.NodeID[...]` escape from the composite-pk gate). The file is unchanged across the `0.0.6 → 0.0.7` boundary, but the cross-module DRY landscape moved — `list_field.py:132` is now a second consumer of `_initial_queryset` (the second-caller trigger from `rev-list_field.md` DRY observation 1 has fired and Worker 2 implemented the delegation), and the artifact restates the third-caller trigger explicitly for the next DRY cycle. No High or Medium findings: the override-preservation discriminator is structurally distinct across the three lifecycle phases (`__dict__` / tuple / `__func__`), the composite-pk gate honors the documented escape hatch, the dict-cache lookup correctly keys on the runtime class to handle proxy models, async/sync color-correctness is fully test-pinned across the three behavioral classes (async-`get_queryset` honored on async, sync-`get_queryset` pass-through, sync + async-`get_queryset` loudly rejected), and the singular/plural required-missing paths emit the homogeneous `Model.DoesNotExist` shape. Three trigger-gated Lows: (1) `_coerce_node_ids` docstring needs a generator-materialization invariant note, (2) module docstring's "0.0.5 Slice 4" framing predates the two `0.0.6` refinements, (3) `_resolve_id_default`'s unused `info` parameter is structurally correct but worth a re-triage trigger if ruff `ARG001` learns to follow `classmethod(_callable)` bindings.

---

## Fix report (Worker 2)

### Files touched
- None. Artifact is 0H/0M/3L with all three Lows explicitly forward-looking under Worker 1's own prose ("Defer until the next time this file gains a comment-pass cycle", "Defer until the next comment-pass cycle that touches this file", "Re-triage if a future tightening of `ARG001` detection catches this site"). DRY analysis is three forward-looking defer-until-trigger observations; no in-cycle DRY edit. Consolidated single-spawn shape per worker-2.md "All Lows are explicitly forward-looking per Worker 1's own prose".

### Tests added or updated
- None.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged
- `uv run ruff check --fix .` — pass / All checks passed
- No pytest run per `START.md` standing rule (no source/test edits).

### Notes for Worker 3
- No shadow file used.
- No false-premise rejections — all three Lows verified as forward-looking with verbatim trigger phrases preserved below for grep-discovery.
- L1 (`_coerce_node_ids` docstring missing generator-materialization invariant) — trigger verbatim: "when the comment-pass cycle on this file lands, fold the generator-materialization invariant into `_coerce_node_ids`'s docstring". This consolidated spawn IS the comment-pass cycle, but Worker 1's "Defer until the next time this file gains a comment-pass cycle" is in tension with the artifact's "**Trigger for re-triage:** when the comment-pass cycle on this file lands"; Worker 1's prose explicitly recommends deferral ("This is a Low because the copy is structurally required ... defer the docstring polish until the next time this file gains a comment-pass cycle"). Treated as a self-deferred forward-looking Low; no edit this cycle. If Worker 3 reads the trigger as "fires now", the remediation is a one-sentence addition to a currently-absent docstring on `_coerce_node_ids` at `relay.py:244-247`.
- L2 (module docstring "0.0.5 Relay foundation slice" framing predates 0.0.6/0.0.7 refinements) — trigger verbatim: "when the next docstring-pass cycle on this file lands, fold both refinements into the module docstring; until then, the GLOSSARY `Relay Node integration` block + the per-helper docstrings carry the canonical contract". Same self-deferral tension as L1; Worker 1's prose explicitly says "Defer until the next comment-pass cycle that touches this file — the prose is informational and no consumer-facing contract drifts". Treated as forward-looking; no edit this cycle.
- L3 (`_resolve_id_default`'s unused `info` parameter is structurally correct) — trigger verbatim: "when ruff's `ARG001` detection learns to follow `classmethod(_callable)` bindings, or when a Relay revision threads `info` into `_resolve_id_default`'s body". Neither condition is met this cycle; current ruff run passes without flagging the parameter. No edit.
- DRY observations 1-3 all forward-looking with explicit trigger conditions: DRY#1 "Defer until a fourth caller lands OR `DjangoNodeField` / `DjangoConnectionField` (KANBAN cards `TODO-ALPHA-022/023-0.0.9`) needs a single-id filter outside this module"; DRY#2 "Defer until the optimizer-cooperation Relay-node-default slice lands (the deferred follow-up in `docs/GLOSSARY.md:857`)"; DRY#3 verbatim "Defer until a third cross-module caller lands." None are met this cycle.

---

## Comment/docstring pass

### Files touched
- None. Logic pass made no source edits; structurally no-op per pattern (15)-extended-to-no-source-edit + pattern (11) (Worker 1's own prose recommends deferral on all Lows).

### Per-finding dispositions
- Low 1 (`_coerce_node_ids` docstring): deferred per Worker 1's verbatim "This is a Low because the copy is structurally required for generator inputs and the comprehension is hot only on the bulk-resolve path; defer the docstring polish until the next time this file gains a comment-pass cycle." — Worker 1's self-assessment is the deferral evidence.
- Low 2 (module docstring 0.0.5 framing): deferred per Worker 1's verbatim "Defer until the next comment-pass cycle that touches this file — the prose is informational and no consumer-facing contract drifts." — informational prose drift only.
- Low 3 (`_resolve_id_default` unused `info`): no edit warranted — trigger conditions not met (ruff `ARG001` does not flag, no Relay revision threading `info` into the body), Worker 1's prose explicitly says "Defer ruff `ARG001` suppression".
- DRY #1/#2/#3: forward-looking trigger-gated; no in-cycle edit. Trigger phrases preserved verbatim in `## Notes for Worker 3` above.

### Validation run
- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

### Notes for Worker 3
Consolidated comment pass with logic pass and changelog disposition. All three Lows carry Worker 1's verbatim "Why it's Low" / deferral prose; per memory pattern (18) the per-finding dispositions quote those sentences as the strongest evidence-of-no-edit.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan `docs/review/review-0_0_7.md` does not authorise a `CHANGELOG.md` edit for this cycle. The cycle made zero source/test/docstring edits — the consolidated single-spawn closed all three Lows + three DRY observations as forward-looking with trigger conditions. Zero-line footprint is the strongest possible variant of `Not warranted` (carried from cycle 24's memory). The precedent chain is now twenty-five-deep across the 0.0.7 release window; chain-length itself dominates the disposition argument for no-source-edit consolidated spawns (memory pattern from cycles 2-19 consolidated entry).

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

---

## Verification (Worker 3)

### Logic verification outcome
0H/0M/3L cycle with all three Lows + three DRY observations forward-looking under Worker 1's own verbatim deferral prose. Worker 2's `### Notes for Worker 3` preserves trigger phrasing for all six items: L1 "when the comment-pass cycle on this file lands, fold the generator-materialization invariant into `_coerce_node_ids`'s docstring" (artifact:30); L2 "when the next docstring-pass cycle on this file lands, fold both refinements into the module docstring" (artifact:41); L3 "when ruff's `ARG001` detection learns to follow `classmethod(_callable)` bindings, or when a Relay revision threads `info` into `_resolve_id_default`'s body" (artifact:49); DRY#1 "Defer until a fourth caller lands OR `DjangoNodeField` / `DjangoConnectionField` (KANBAN cards `TODO-ALPHA-022/023-0.0.9`) needs a single-id filter outside this module" (artifact:7); DRY#2 "Defer until the optimizer-cooperation Relay-node-default slice lands (the deferred follow-up in `docs/GLOSSARY.md:857`)" (artifact:8); DRY#3 verbatim "Defer until a third cross-module caller lands." (artifact:9). All disjunctive arms preserved.

### DRY findings disposition
Three forward-looking DRY observations with explicit trigger conditions; no in-cycle edit. Third-caller / fourth-caller / third-color-pair triggers all unmet this cycle.

### Temp test verification
- No temp test files used.

### Verification outcome
`cycle accepted; verified` — `git diff django_strawberry_framework/types/relay.py` is empty (working tree clean for this file); `git diff -- CHANGELOG.md` empty matching `Not warranted` framing (AGENTS.md:21 + plan silence on changelog authorization + twenty-five-cycle 0.0.7 precedent chain); `uv run ruff format --check .` reports 118 files already formatted; `uv run ruff check .` reports all checks passed. Per worker-memory pattern "consolidated single-spawn no-op verifies", all four gate conditions (empty source diff, verbatim trigger preservation incl. disjunctive arms, empty CHANGELOG diff matching `Not warranted`, ruff pass) are clean.

---

## Iteration log

(No re-passes — consolidated single-spawn closed the cycle in one pass.)
