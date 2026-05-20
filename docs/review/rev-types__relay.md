# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## DRY analysis

- Extract `_model_for(type_cls) -> type[models.Model]` collapsing `cls.__django_strawberry_definition__.model` reads at `types/relay.py:78`, `134`, `297`. `_initial_queryset` (`types/relay.py:264-271`) already absorbs the QuerySet-variant call site; a sibling `_model_for` would single-source the model-only reads and make the "type_cls is a registered DjangoType with a definition" contract visible in one named place. Three sites today, with `install_is_type_of` being the structural outlier (class-creation phase, not finalize phase).

## High:

None.

## Medium:

### Async/sync sibling-pair structural duplication is at the threshold where a shared assembler would buy back readability

`_resolve_node_default` + `_resolve_node_async` (`types/relay.py:311-344`, `347-365`) and `_resolve_nodes_default` + `_resolve_nodes_async` (`types/relay.py:368-408`, `411-434`) each express the same five-step recipe: derive `id_attr` from `cls.resolve_id_attr()`, run the get_queryset hook (sync = guarded against returned coroutine; async = `await`-ed), apply the id filter, then materialize via `.get`/`.first`/`.aget`/`.afirst` (single-id) or `_order_nodes` (multi-id). The only branch that genuinely differs is the get_queryset hook and the queryset materialization — every other line is identical. Why it matters: the four resolvers must stay in lockstep across future spec changes (Decision 9's contract evolves; new error paths land); today the lockstep is enforced by the test suite (`test_resolve_node_*`, `test_resolve_nodes_*`, `test_resolve_*_async_*` — 30+ tests pinning the shape) but the code structure does not surface the parallel. The recommended consolidation is *not* to collapse the sync/async pair (the function-color split is intentional and load-bearing) but to extract a `_apply_id_filter_and_materialize_single(qs, id_attr, *, node_id, required, async_path: bool)` and a `_apply_id_filter_and_materialize_many(qs, coerced_keys, id_attr, *, required, async_path: bool)` so the four call sites become three lines each. This is at the Medium threshold per the worker-memory calibration ("three-axis-sibling drift IS the bug … the asymmetric outlier is Medium even if practical risk is low") — today they DON'T drift; the structural pattern is documented in the per-function docstrings; the risk is a future maintainer changing one path without the other.

```django_strawberry_framework/types/relay.py:339:344
    id_attr = cls.resolve_id_attr()
    if in_async_context():
        return _resolve_node_async(cls, id_attr, node_id, info=info, required=required)
    qs = _apply_get_queryset_sync(cls, _initial_queryset(cls), info)
    qs = _apply_node_filter(qs, id_attr, node_id=node_id)
    return qs.get() if required else qs.first()
```

```django_strawberry_framework/types/relay.py:399:408
    id_attr = cls.resolve_id_attr()
    if in_async_context():
        return _resolve_nodes_async(cls, id_attr, node_ids, info=info, required=required)
    qs = _apply_get_queryset_sync(cls, _initial_queryset(cls), info)
    coerced_ids = _coerce_node_ids(node_ids)
    qs = _apply_node_filter(qs, id_attr, node_ids=coerced_ids)
    if coerced_ids is None:
        return qs
    coerced_keys = [str(node_id) for node_id in coerced_ids]
    return _order_nodes(cls, list(qs), coerced_keys, id_attr, required=required)
```

## Low:

### `_check_composite_pk_for_relay_node` invokes `cls.resolve_id_attr()` mid-pipeline before `install_relay_node_resolvers` runs — relies on inherited `relay.Node.resolve_id_attr`

The composite-pk gate is invoked at `types/finalizer.py:237` strictly between `apply_interfaces` (`finalizer.py:235`) and `install_relay_node_resolvers` (`finalizer.py:238`). At that moment, `type_cls.resolve_id_attr` is the upstream `relay.Node.resolve_id_attr` classmethod (because the framework default has not been installed yet but `relay.Node` IS in the MRO). That upstream implementation is precisely what the gate wants — it raises `NodeIDAnnotationError` when no consumer `NodeID[...]` annotation exists, and the gate catches that to confirm the consumer has no escape hatch and to re-raise as `ConfigurationError`. This is correct, but the dependency on phase ordering and on upstream Strawberry behavior is not explicit at the call site. A `# Phase 2.5 ordering note: this calls upstream relay.Node.resolve_id_attr (our default is installed after this gate runs).` comment at `types/relay.py:138` would pin the ordering invariant. Low because the test suite (`test_composite_pk_with_explicit_node_id_annotation_is_accepted` at `tests/types/test_relay_interfaces.py:240-258`) covers the contract, so a future re-ordering would break loudly; the comment is a documentation polish.

```django_strawberry_framework/types/relay.py:136:142
    if not isinstance(model._meta.pk, CompositePrimaryKey):
        return
    try:
        type_cls.resolve_id_attr()  # type: ignore[attr-defined]
    except NodeIDAnnotationError:
        pass
    else:
        return
```

### `_apply_node_filter` with both `node_id=None` and `node_ids=None` silently returns the unfiltered queryset

The helper has three branches: `node_id is not None` (filter `=`), `node_ids is not None` (filter `__in=`), and else (no filter applied). The else branch is reachable from `_resolve_nodes_default` when `node_ids` is `None` (intentional — the Decision 3 four-step shape returns the unfiltered queryset for bulk fetch); it is NOT reachable from `_resolve_node_default` because Strawberry always passes a `node_id`. If Strawberry's call shape changes (or a consumer calls the resolver directly with `node_id=None`), the resolver returns `qs.first()` — the first arbitrary row — silently. The risk surface is small (consumer reaching for an internal `_resolve_node_default`), but a `assert node_id is not None or node_ids is not None, "internal contract: at least one of node_id/node_ids must be set"` would convert silent dead branch into a loud one. Low because the entry-point `_resolve_node_default` doesn't expose `node_ids` and the test suite pins the documented Strawberry call shape; the defensive `assert` is a polish.

```django_strawberry_framework/types/relay.py:256:261
    if node_id is not None:
        coerced = _coerce_node_id(node_id)
        return qs.filter(**{id_attr: coerced})
    if node_ids is not None:
        return qs.filter(**{f"{id_attr}__in": node_ids})
    return qs
```

### `_resolve_id_default` keys the `__dict__` lookup on `root.__class__._meta.pk.attname` rather than the framework-bound `cls`'s model

The framework-bound `cls.__django_strawberry_definition__.model` is the *declared* model on the DjangoType. `root.__class__._meta` is the *actual* class of the queried row. For concrete Django models the two agree, but for proxy models or model inheritance (concrete + abstract), they can diverge. The current behavior — keying on `root.__class__` — is the *safer* choice for cache-lookup correctness because `root.__dict__` keys reflect `root.__class__`'s actual pk attname. Worth a one-line docstring callout that the choice is deliberate (the `cls.__django_strawberry_definition__.model._meta.pk.attname` alternative would mis-key for proxy-model rows). Low because the test suite (`test_resolve_id_uses_dict_cache`, `test_resolve_id_falls_back_to_getattr`) pins behavior but doesn't pin the proxy-model concern explicitly.

```django_strawberry_framework/types/relay.py:183:189
    id_attr = cls.resolve_id_attr()
    if id_attr == "pk":
        id_attr = root.__class__._meta.pk.attname
    try:
        return str(root.__dict__[id_attr])
    except KeyError:
        return str(getattr(root, id_attr))
```

### `_apply_node_filter` docstring says "sync; no get_queryset involvement" but the function is also called from the async resolver pair

`_apply_node_filter` is a pure ORM helper invoked from both `_resolve_node_default` / `_resolve_nodes_default` and `_resolve_node_async` / `_resolve_nodes_async`. The "sync; no get_queryset involvement" docstring qualifier reads as "this is the sync code path" when in fact it is the *function-color-agnostic* portion of the recipe (the lazy `.filter` call is identical for sync and async resolvers; only the terminal `.get`/`.aget` differs). Reword to "color-agnostic; the lazy `.filter` call is identical on sync and async paths; the terminal materialization is what differs." Low — docstring nit.

```django_strawberry_framework/types/relay.py:250:255
    """Apply the Relay-id filter to ``qs`` (sync; no get_queryset involvement).

    The post-``get_queryset`` queryset is sync-iterable (or
    async-iterable in the async branch); the filter itself is a pure ORM
    operation and identical across both paths.
    """
```

### Three remaining `cls.__django_strawberry_definition__.model` reads (78, 134, 297) skip the `_initial_queryset` centralization gesture

`_initial_queryset` (`types/relay.py:264-271`) extracts `cls.__django_strawberry_definition__.model._default_manager.all()` into one place — but the three other reads of `.model` (without `.objects.all()`) at lines 78, 134, 297 stay inline. A `_model_for(type_cls) -> type[models.Model]` helper would single-source the "type_cls is a registered DjangoType with a definition" contract and align with the existing `_initial_queryset` pattern. Low because the three sites are read-only one-line reads and the existing docstrings make the contract explicit; the helper is a polish, not a defect.

```django_strawberry_framework/types/relay.py:78
    model = type_cls.__django_strawberry_definition__.model
```

```django_strawberry_framework/types/relay.py:134
    model = type_cls.__django_strawberry_definition__.model
```

```django_strawberry_framework/types/relay.py:297
    model = cls.__django_strawberry_definition__.model
```

## What looks solid

### DRY recap

- **Existing patterns reused.** Calls into the registered-type contract `cls.__django_strawberry_definition__.model` set up by `types/base.py:222-244` (`DjangoTypeDefinition` construction in `__init_subclass__`); reuses the `relay.Node`-identity predicate `issubclass(..., relay.Node)` that is the same lower-bound used in `types/base.py:137` (`_is_relay_shaped`); reuses `strawberry.utils.inspect.in_async_context` for the async-routing gate. The composite-pk gate at `types/relay.py:135` mirrors the `isinstance(..., CompositePrimaryKey)` shape from Django 5.2+ (one site only — no sibling using the same predicate today). `_RELAY_RESOLVER_DEFAULTS` (`types/relay.py:440-445`) is the local "single source of truth" pattern (same shape as `types/base.py:48-56` `DEFERRED_META_KEYS`, `types/base.py:65-75` `_VALIDATED_FIELDS`).
- **Duplication risk in the current file.** `cls.__django_strawberry_definition__.model` reads at lines 78, 134, 271, 297 (three direct + one through `_initial_queryset`); `cls.resolve_id_attr()` reads at lines 138, 183, 339, 399; `_coerce_node_ids` then `_apply_node_filter` then conditional `_order_nodes` reads as a near-identical four-line motif across `_resolve_nodes_default:402-408` and `_resolve_nodes_async:427-434` (the *only* difference is `await` placement on the get_queryset hook and async-comprehension materialization at line 433). The async/sync sibling pair `_resolve_node_default` + `_resolve_node_async` show the same shape at the single-id scope (`types/relay.py:339-344` vs `347-365`). Two distinct literal duplications: `f"{id_attr}__in"` (line 260) and the pair-comparison `existing_func is not None and existing_func is node_func` is single-sited; `__func__` literal appears in module docstring + AST attribute lookups at lines 14, 455, 461, 470, 471 (2x repeated literals reported by the helper) — load-bearing, not a finding. The async/sync structural duplication is tracked as the Medium M1 finding above.

### Other positives

- The four-resolver `__func__` identity-discriminator at `install_relay_node_resolvers` (`types/relay.py:467-473`) is the right shape for the "consumer override wins, framework default fills the gap" contract — distinct from the `cls.__dict__` membership check at `install_is_type_of:76` (declared-on-this-class semantics) and from the `relay.Node in interfaces` tuple-membership check at `_build_annotations` (collection-time semantics). Three structurally-distinct discriminators at three lifecycle phases, each test-pinned (`test_install_relay_node_resolvers_idempotent`, `test_install_relay_node_resolvers_preserves_consumer_override`, `test_consumer_resolve_*_wins` family).
- `apply_interfaces` MRO-mutation guard is correct and complete: idempotent via `iface not in type_cls.__mro__` (so `apply_interfaces` re-running after a Phase-2.5 partial failure is a no-op per `finalizer.py:152-153`), and the `TypeError` wrap surfaces the offending interface name in the consumer-visible error rather than Python's opaque layout TypeError. Test coverage at `test_apply_interfaces_skips_already_present_bases` and `test_apply_interfaces_wraps_typeerror_as_configuration_error`.
- The composite-pk gate honors its own remediation. The "escape hatch" path is end-to-end-tested by `test_composite_pk_with_explicit_node_id_annotation_is_accepted` — a consumer who writes `id: relay.NodeID[str]` on a composite-pk model bypasses the gate, and the test pins both that bypass and the resulting `resolve_id_attr` return value.
- Decision 9 async/sync get_queryset honoring: the sync path *rejects* a returned coroutine with `ConfigurationError` (not silent `AttributeError` on `.filter`); the async path awaits regardless of consumer color. Both paths covered by `test_resolve_node_sync_with_async_get_queryset_raises`, `test_resolve_nodes_sync_with_async_get_queryset_raises`, `test_resolve_node_async_awaits_async_get_queryset`, and `test_resolve_nodes_async_awaits_async_get_queryset`.
- `_RELAY_RESOLVER_DEFAULTS` (`types/relay.py:440-445`) is the canonical single-source-of-truth pattern the codebase rewards (same shape as `DEFERRED_META_KEYS`, `_VALIDATED_FIELDS`); the comment at lines 437-439 names that it "appears nowhere else," anchoring the invariant.
- Sentinel-discipline + repr-shaping pattern is consistent: this module has no consumer-surfaced sentinels of its own, but it consumes the upstream `NodeIDAnnotationError` sentinel-exception-pattern via `try/except NodeIDAnnotationError: ...` at `_check_composite_pk_for_relay_node` and `_resolve_id_attr_default` — symmetric handling at two sites, each correct for its phase.

### Summary

`types/relay.py` is a 473-line, dense, well-tested module that ports four lifecycle-distinct discriminators from `strawberry_django` (`is_type_of`, `apply_interfaces` MRO injection, `_check_composite_pk_for_relay_node`, and the `__func__`-identity-based `install_relay_node_resolvers`) plus the four default Relay resolvers (`_resolve_id`, `_resolve_id_attr`, `_resolve_node`, `_resolve_nodes`) with sync+async sibling pairs honoring Decision 9. Logic is sound; no High findings; no Medium findings other than the sync/async-sibling-pair structural duplication that is at the threshold where a `_apply_id_filter_and_materialize_*` assembler would buy back readability. Five Low findings cluster around documentation polish (phase-ordering note at the composite-pk gate, docstring color-agnosticism wording at `_apply_node_filter`, proxy-model rationale at `_resolve_id_default`) and a single shared structural DRY gesture (`_model_for(type_cls)` to align the three remaining `__django_strawberry_definition__.model` reads with the existing `_initial_queryset` centralization). The `__func__` identity discriminator and the three structurally-distinct lifecycle-phase discriminators are the module's load-bearing pattern and earn a "What looks solid" callout. Carry forward to the folder pass: confirm the `__func__`-identity vs `cls.__dict__`-membership vs `relay.Node in interfaces` three-axis discriminator pattern stays single-sited and that no new sibling slips in with a fourth discriminator shape.

## Fix report (Worker 2)

**Pass:** logic pass (L2 only; M1/L5 deferred per dispatch).

**Disposition by item:**

- **L2 — defensive `assert` in `_apply_node_filter`:** ATTEMPTED, then REVERTED. The artifact's contract claim was wrong: the else branch IS reached on the existing public path. `_resolve_nodes_default` (line 401-411) is documented to support `node_ids=None` for the "bulk-fetch / no ids -> full queryset" shape; `_coerce_node_ids(None)` returns `None` at line 238-239; that `None` is then passed as `node_ids=None` to `_apply_node_filter` at line 407. Adding the assert immediately failed `tests/types/test_relay_interfaces.py::test_resolve_nodes_without_ids_returns_full_queryset` (which calls `CategoryNode.resolve_nodes(info=None)` with no ids and expects the unfiltered queryset). The "silent no-filter fallthrough" is not a latent bug — it is the spec'd contract for the `node_ids=None` bulk path, and the artifact's framing ("if Strawberry's call shape changes... silently returns first arbitrary row") conflates two different entry points: `_resolve_node_default` (single-id, never reaches the else) and `_resolve_nodes_default` (multi-id, intentionally reaches the else when `node_ids is None`).

  The corrective assertion would have to read `assert node_id is not None or node_ids is not None or <caller is _resolve_nodes_default>`, which is not expressible at the helper boundary without leaking caller identity. The cleaner shape (if the polish is worth pursuing in a later cycle) is to split the helper into `_apply_node_id_filter(qs, id_attr, node_id)` and `_apply_node_ids_filter(qs, id_attr, node_ids_or_none)` so the single-id helper can carry the assert while the multi-id helper keeps the documented `None` -> pass-through contract. Surface this re-framing to the next reviewer rather than implementing it here — out of dispatch scope.

- **M1 — async/sync resolver pair duplication helper extraction:** DEFERRED to follow-up cycle per dispatch.
- **L1, L3, L4:** comment pass — out of scope for this logic pass.
- **L5 — `_model_for(type_cls)` helper extraction:** DEFERRED to follow-up cycle per dispatch.

**Validation:**

- `uv run ruff format .` — 101 files unchanged (pass).
- `uv run ruff check --fix .` — all checks passed.
- `uv run pytest tests/types/ -x -k "relay or node"` — 75 passed, 169 deselected. (Coverage fail-under is expected for `-k`-filtered runs; `types/relay.py` itself reports 100%.)

**Net source change:** none. The repository's `types/relay.py` is byte-identical to its pre-dispatch state.

**Notes for Worker 3:** The L2 stop condition fired exactly as dispatch anticipated ("If any test fails because of the new assertion ... revert the assert and surface — the contract claim was wrong"). The contract claim was wrong; reverted. Treat L2 as **rejected on attempt** rather than implemented. The disposition above proposes the split-helper shape as a follow-up path if a future cycle wants to recover the defensive-assert intent without breaking the documented bulk-fetch contract.

## Comment / docstring pass (Worker 2)

**Pass:** combined comment + changelog pass.

**Edits made:**

- **L1 — Phase 2.5 ordering note at the composite-pk gate.** Added an inline comment at `types/relay.py:138` (immediately before the `try: type_cls.resolve_id_attr()` call inside `_check_composite_pk_for_relay_node`): "Phase 2.5 ordering note: this calls upstream `relay.Node.resolve_id_attr` (our default is installed after this gate runs)." Pins the ordering invariant Worker 1 surfaced: the gate runs between `apply_interfaces` and `install_relay_node_resolvers` in `finalizer.py`, so `cls.resolve_id_attr` here is the upstream classmethod, not the framework default. Verbatim wording per dispatch.
- **L3 — proxy-model docstring callout on `_resolve_id_default`.** Added a paragraph to the existing `_resolve_id_default` docstring (around `types/relay.py:183`) noting that keying the `__dict__` lookup on `root.__class__._meta.pk.attname` is deliberate, because the alternative `cls.__django_strawberry_definition__.model._meta.pk.attname` would mis-key for proxy-model rows whose actual class differs from the declared DjangoType model.
- **L4 — `_apply_node_filter` docstring reword.** Replaced the misleading "sync; no get_queryset involvement" qualifier with "color-agnostic" framing, naming sync (`.get`/`.first`) and async (`.aget`/`.afirst`) terminal materializations as the only branch-specific surface. The lazy `.filter` call itself is identical across both paths, per the function-color-agnostic shape Worker 1 surfaced.

**Deferred / not done:**

- **M1 (async/sync helper extraction):** deferred to follow-up cycle per dispatch.
- **L5 (`_model_for(type_cls)` helper extraction):** deferred to follow-up cycle per dispatch.
- **L2:** rejected on attempt during the logic pass (artifact's contract claim was wrong; reverted; split-helper proposed for a future cycle).

**Validation:**

- `uv run ruff format .` — 101 files unchanged (pass).
- `uv run ruff check --fix .` — all checks passed.

**Net source change:** three docstring / comment edits in `types/relay.py`. No logic change.

## Changelog disposition (Worker 2)

**Disposition:** not warranted.

**Reason:** The only edits this cycle are three internal docstring / comment improvements in `types/relay.py` (L1 inline-comment phase-ordering note, L3 proxy-model docstring callout on `_resolve_id_default`, L4 reworded `_apply_node_filter` color-agnostic docstring). No public surface change, no behavior change, no test surface change. Worker 2's logic-pass attempt at L2 was reverted with no net source change. M1 and L5 were dispatch-deferred to follow-up cycles.

**Action:** none. `CHANGELOG.md` is not edited. Pre-alpha rule per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") plus the active review plan's silence on this cycle → default-to-not-edit.

## Verification (Worker 3, pass 2)

- L1 (Phase 2.5 ordering note at the composite-pk gate, near `types/relay.py:138`) accepted: inline comment names upstream `relay.Node.resolve_id_attr` and pins the install-order invariant Worker 1 surfaced.
- L3 (proxy-model docstring callout on `_resolve_id_default`) accepted: paragraph explains why keying on `root.__class__._meta.pk.attname` is deliberate vs the declared DjangoType model, anchoring the proxy-model concern Worker 1 named.
- L4 (`_apply_node_filter` docstring reword) accepted: misleading "sync; no get_queryset involvement" qualifier replaced with color-agnostic framing naming sync (`.get`/`.first`) and async (`.aget`/`.afirst`) terminal materializations as the only branch-specific surface.
- Deferrals recorded: M1 (async/sync resolver pair helper extraction) and L5 (`_model_for(type_cls)` helper extraction) deferred to follow-up cycle per dispatch; both are surfaced in the Comment-pass section so the next reviewer can pick them up.
- L2 rejected as false premise during logic pass — recorded in the Fix report section with the failing test name (`test_resolve_nodes_without_ids_returns_full_queryset`) and the split-helper shape proposed for any future cycle that wants to recover the defensive-assert intent.
- Changelog disposition "not warranted" accepted: `git diff -- CHANGELOG.md` empty; rationale dual-cites the `AGENTS.md` changelog ban AND the active plan's lack of authorization; the in-cycle source delta is three internal docstring/comment edits with no public surface, behavior, or test surface change.

Verification outcome: cycle accepted; verified.
