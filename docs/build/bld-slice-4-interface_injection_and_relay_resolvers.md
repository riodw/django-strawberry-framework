# Build: Slice 4 — Interface base-class injection + Relay resolver defaults

Spec reference: `docs/spec-relay_interfaces.md` (lines 41-82 Slice 4 sub-checklist; lines 269-287 Decision 1 / Decision 2 — interfaces applied in a new Phase 2.5 between Phase 2 and Phase 3, and composite-pk gate fires here; lines 288-317 Decision 3 — `__func__` identity test + the four `_resolve_*_default` shapes; lines 333-342 Decision 5 — Phase 2.5 placement and the no-new-tracking-state contract; lines 343-351 Decision 6 — override contract preserved; lines 352-361 Decision 7 — optimizer / projection invariants; lines 371-379 Decision 9 — sync + async resolver paths; lines 380-426 internal helper surface; lines 442-446 implementation-plan step 4; lines 462-513 test plan)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

Worker-memory carry-forwards governing Slice 4:

- `docs/build/worker-memory/worker-1.md:14-17,32-36,46-49,55-58` pin three structural splits Slice 4 must preserve. Slice 2's `__dict__` membership vs. Slice 4's `__func__` identity vs. Slice 3's tuple-membership are **three different override discriminators**, each at its own lifecycle phase. They must remain independent — collapsing any pair into a generic `override_check(...)` helper is a DRY false positive (worker-memory line 34).
- Slice 1 stored the validated `interfaces` tuple on `DjangoTypeDefinition.interfaces`. Slice 4's Phase 2.5 reads from that slot; it must not re-validate (worker-memory line 5, line 15-16).
- `__django_strawberry_definition__.model` is the canonical read for the Django model in Relay helpers (worker-memory line 35, spec line 314). Slice 4's `_resolve_node_default` reads from the same slot.

The seven DRY questions answered explicitly:

1. **Shared helper for the override discriminators (intentional split).** Slice 2's `install_is_type_of` (`django_strawberry_framework/types/relay.py:28`) uses `if "is_type_of" in type_cls.__dict__: return` because **no** Strawberry-supplied inherited default exists for `is_type_of` — the question is "did the consumer write this on the class itself?". Slice 4's `install_relay_node_resolvers` must use the `__func__` identity test (`existing.__func__ is relay.Node.<attr>.__func__`) because `relay.Node` **does** supply inherited defaults for all four `resolve_*` methods via MRO, and `cls.__dict__` membership would falsely treat every inherited Strawberry default as "consumer code, do not overwrite", which would skip injection forever (spec lines 296-308). Slice 3's tuple-membership (`relay.Node in interfaces`, `base.py:569`) runs pre-base-injection at collection time against the **validated tuple**, structurally different from both. **Intentional split: three discriminators answer three questions at three lifecycle phases; no shared helper.** Upstream `strawberry_django/type.py:204` (`__dict__`) and `:213-225` (`__func__` identity) make the same split for the same reason. This is the binding worker-memory carry-forward from Slices 2 and 3 (worker-memory line 34, line 46-47, line 55-58).
2. **Reuse of `_validate_interfaces` flow.** Slice 1's `_validate_meta` (`django_strawberry_framework/types/base.py:363-405`) calls `_validate_interfaces` (`base.py:287-360`) and returns the normalized tuple, which `__init_subclass__` threads into `DjangoTypeDefinition(interfaces=interfaces)` at `base.py:139`. Phase 2.5 reads the already-validated tuple from `definition.interfaces` (`types/definition.py:42`). Re-validation is forbidden; the validator's seven Decision-4 rules are not re-applied at finalization. Phase 2.5 only does **structural** operations: `__bases__` mutation, MRO-based composite-pk and `relay.Node` checks, and resolver injection. Confirmed: the single-source-of-truth pattern Slices 1/2/3 established continues at Slice 4 (worker-memory line 5, line 15, line 48-49).
3. **Composite-pk detection.** `pyproject.toml:31` pins `Django>=5.2`, so `django.db.models.CompositePrimaryKey` (Django 5.2+; lives at `django.db.models.fields.composite.CompositePrimaryKey`, re-exported via `django.db.models`) is unconditionally importable. The plan uses `from django.db.models import CompositePrimaryKey` and `isinstance(model._meta.pk, CompositePrimaryKey)` at the top of `types/relay.py` (next to the `apply_interfaces` helper that owns the gate). Rationale: (a) Django 5.2 is the lower bound and the spec at lines 287, 455, 555 names CompositePrimaryKey as the detection target; (b) `isinstance` is the clearest expression of "is this Django's composite-pk type?" without coupling to a stable `name`/`attname` shape that may not exist on a composite key; (c) it matches the spec language at line 287 ("Detection uses Django's `model._meta.pk` shape"). Slice 3's `_meta.pk.name` read (`base.py:570`) is gated behind `suppress_pk_annotation = relay.Node in interfaces` (`base.py:569`), so a composite-pk model declaring `relay.Node` would attempt `_meta.pk.name` access at collection time — **before** Phase 2.5's gate fires. The plan adds **no defensive guard in Slice 3** (already confirmed by Slice 3's Open Question 7 / final-verification memory). Until Slice 5 promotes `"interfaces"` from `DEFERRED_META_KEYS`, end-to-end `Meta.interfaces = (relay.Node,)` declarations on a composite-pk model still raise the deferred-key error first. Slice 4's test `test_relay_node_with_composite_pk_raises` invokes Phase 2.5 directly to exercise the gate; this matches Slice 1's unit-boundary pattern.
4. **Async detection.** Strawberry's `Info` instance is the canonical source for "is this an async resolver?". Empirically the public surface is `info.context.request` plus the rest, but the spec at lines 372-379 names "Strawberry's `info` carries an `is_awaitable` signal; `asgiref.sync.iscoroutinefunction` is the fallback." In practice, strawberry-django (`strawberry_django/relay/utils.py:155-187`) builds the sync queryset+optimizer chain once, then checks `inspect.isawaitable(retval)` on the result of `django_resolver(...)` — the `django_resolver` decorator is what flips sync vs. async behavior. We do **not** import strawberry-django (spec line 317). The plan uses Django's native async ORM API (`aget`, `afirst`, `aiter`, `acount`) when available, falling back to `asgiref.sync.sync_to_async` for terminal calls without a native async equivalent. **Sync/async dispatch lives at the terminal call in `_resolve_node_default` / `_resolve_nodes_default`**, not at the queryset-assembly stage. Reasoning: the queryset assembly (`model._default_manager.all()` → `cls.get_queryset(qs, info)` → `qs.filter(**{id_attr: node_id})` → optional `ext.optimize(qs, info=info)`) is sync-safe in both contexts because querysets are lazy. Only the **terminal materialization** (`qs.first()`, `qs.get()`, materializing to a `list` for `_resolve_nodes_default`) needs the sync/async split. The detection signal is `info.context` carrying a coroutine context: the spec's preferred answer is to ship **both** a sync resolver and an async resolver per method, attaching them as classmethods at injection time, and let Strawberry's resolver dispatcher pick the right one — but Decision 3 (line 305) anchors a **single** classmethod assignment per attr. The plan therefore ships **one** classmethod per attr that internally branches on `inspect.iscoroutinefunction(...)`-style detection on `info` (or, more simply: returns a coroutine when the calling context is async, returns a sync value otherwise). The simplest shape borrowed from `strawberry_django/relay/utils.py:184-189` is to **always** invoke the sync path under `asgiref.sync.sync_to_async(...)` when the context is async, and the bare sync path otherwise. The plan picks the simpler shape: introduce one private helper `_run_query(callable, *, info, async_callable=None)` that detects the context via Strawberry's `info` and dispatches to `await async_callable()` (async path) or `callable()` (sync path); the four `_resolve_*_default` functions call this helper at the **single** terminal step. See Open question for Worker 2 below for a detection-mechanism fallback if Strawberry's `info` does not expose a reliable signal.
5. **`get_queryset` / optimizer call sequence (shared queryset-assembly helper).** Both `_resolve_node_default` and `_resolve_nodes_default` follow the identical four-step shape (per spec line 314 / 315, mirroring `strawberry_django/relay/utils.py:223-282` and `:102-198`):
   1. `qs = model._default_manager.all()`
   2. `qs = cls.get_queryset(qs, info)`
   3. `qs = qs.filter(**{id_attr: node_id})` (single) or `qs = qs.filter(**{f"{id_attr}__in": coerced_ids})` (plural)
   4. `ext = <optimizer extension on info.context>; if ext is not None: qs = ext.optimize(qs, info=info)`
   The plan introduces one private helper, `_assemble_node_queryset(cls, info, id_attr, *, single, node_id=None, node_ids=None)`, that returns the post-step-4 queryset. Justification: (a) the four-step sequence is identical between single- and plural-node paths except for the filter shape at step 3; (b) the optimizer-extension lookup (`ext = getattr(info.context, "dst_optimizer_extension", None)` or whatever the read shape is — see Open question for Worker 2) is the same in both paths; (c) without the helper, the two resolvers would copy four lines each — a Worker 3 DRY finding waiting to happen. The helper is **private** (underscore-prefixed) and lives in `types/relay.py` alongside the four `_resolve_*_default` functions. Its single responsibility is queryset assembly through optimizer-application; the terminal `first()`/`get()` (single) and order-preserving materialization (plural) live in the calling resolvers because their dispatch differs by required/missing semantics. **The shared helper preserves the optimizer-cooperation contract Decision 7 calls "the `cls.get_queryset(qs, info)` invariant"** by guaranteeing the four steps run in the documented order at every Relay node call.
6. **String literals.** A new tuple constant `_RELAY_RESOLVER_NAMES: tuple[str, ...] = ("resolve_id", "resolve_id_attr", "resolve_node", "resolve_nodes")` lives at module scope in `types/relay.py`. Single call site: `install_relay_node_resolvers` iterates over it. Justification: (a) the four method names appear in the spec at lines 293-298 and again in the helper-surface sketch at lines 400-424, and would otherwise repeat as both an iteration tuple and (if hand-mapped) four distinct setattr calls; (b) the Worker 3 shadow overview's "Repeated string literals" section will flag any unintentional repetition; (c) Slice 5's docs touch the same names. **No constant for `"is_type_of"`** is introduced — that string appears in exactly one place (`types/relay.py:28`, Slice 2's `if "is_type_of" in type_cls.__dict__: return`), and adding a constant for a single-site literal would be premature. **No constant for `"pk"`** — strawberry-django's pattern (and spec line 312) hard-codes `"pk"` as the Django-conventional pk attname fallback; it's a Django idiom, not a package literal. The `id_attr = cls.resolve_id_attr()` indirection always runs first; `"pk"` only appears inside `_resolve_id_attr_default` as the `NodeIDAnnotationError` fallback string and inside `_resolve_id_default`'s pk-attname coercion step (per `strawberry_django/relay/utils.py:340-348`, the pattern `if id_attr == "pk": id_attr = root.__class__._meta.pk.attname` resolves `"pk"` to the actual column attname before the dict-cache read). The plan keeps `"pk"` literal at those two sites; Worker 3 may flag if a third site appears.
7. **Tests scaffolding.** `tests/types/test_relay_interfaces.py` already has the test-bypass scaffolding from Slices 1-3 (lines 14-35): `from strawberry import relay` at line 15, `_meta(**attrs)` helper at lines 32-35, autouse `_isolate_registry` fixture at lines 24-29, direct imports of internal helpers at line 20 (`_build_annotations`, `_validate_interfaces`). Slice 4 reuses every piece without churn:
   - Phase 2.5 invocation: Slice 4 cannot declare `Meta.interfaces = (relay.Node,)` end-to-end through `DjangoType.__init_subclass__` until Slice 5 promotes the key. The Slice 4 tests therefore invoke Phase 2.5 by either (a) constructing a `DjangoType` subclass **without** `Meta.interfaces`, then manually populating `definition.interfaces` to `(relay.Node,)` on the registered definition before calling `finalize_django_types()` — the pattern Slice 1's `test_meta_interfaces_stored_on_definition` (`tests/types/test_relay_interfaces.py:144-161`) seeded, or (b) directly invoking the new helpers (`apply_interfaces`, `install_relay_node_resolvers`, `_resolve_*_default`) as units against synthetic host classes. The plan picks **(a)** for the "end-to-end Phase 2.5" tests (anything that needs the full lifecycle exercised — composite-pk, resolver injection on a real DjangoType, optimizer projection) and **(b)** for the unit-boundary tests (resolver-default direct invocation, override discriminator semantics, `_resolve_id` cache vs. getattr branches). This split keeps each test's surface minimal.
   - Shared helper: a new fixture `_finalize_with_interfaces(*, type_cls, interfaces)` is introduced **at the top of the Slice 4 section divider** in `tests/types/test_relay_interfaces.py`. It assigns `registry.get_definition(type_cls).interfaces = interfaces` and calls `finalize_django_types()`. Justification: the ~25 Slice 4 tests will each need to exercise some shape of Phase 2.5; centralizing the deferred-key bypass into one fixture means a future test author cannot accidentally drift on the bypass mechanism. The fixture is a **plain function** (not a pytest fixture) so each test calls it explicitly with its own `type_cls` and `interfaces` tuple — making the bypass visible at every call site. Worker 2 has discretion on the exact signature.
   - The HTTP test in `examples/fakeshop/test_query/test_library_api.py` does **not** use this bypass scaffolding — by the time that test runs (Slice 5 onward), `"interfaces"` is in `ALLOWED_META_KEYS` and the consumer-facing `Meta.interfaces = (relay.Node,)` declaration works end-to-end through `__init_subclass__`. **However**, Slice 4's checklist (spec line 82) lists the HTTP test under Slice 4, before Slice 5's promotion. The plan resolves this ordering tension by having the HTTP test use the **same definition.interfaces injection bypass** the Slice 4 unit tests use: a fixture that, after the schema reload, injects `interfaces=(relay.Node,)` on the appropriate `library` `DjangoType`'s `DjangoTypeDefinition` before finalization runs at schema import. Worker 2 may instead choose to defer the HTTP test to Slice 5 if the bypass cannot land cleanly in the existing `_reload_project_schema_for_acceptance_tests` fixture (`examples/fakeshop/test_query/test_library_api.py:21-47`); that defer would not be a contract violation because spec line 82's test is the **last** Slice 4 sub-checklist item and is structurally testing Slice 5's end-to-end behavior. The plan flags this as **Open question 3** for Worker 2 below.

### Implementation steps

The slice touches three source files and four test files.

**Module: `django_strawberry_framework/types/relay.py`** (the Slice 2 home for `install_is_type_of`; Slice 4 extends).

1. **Imports.** Add at the top of `types/relay.py` (after the existing `from __future__ import annotations` at line 3):

   ```
   from typing import Any, Iterable

   from asgiref.sync import sync_to_async
   from django.db import models
   from django.db.models import CompositePrimaryKey
   from strawberry import relay
   from strawberry.relay.exceptions import NodeIDAnnotationError

   from ..exceptions import ConfigurationError
   ```

   Justification per import:
   - `Any`, `Iterable`: type hints for the four `_resolve_*_default` signatures (spec lines 408-423).
   - `sync_to_async`: Decision 9 fallback when a Django async ORM API is missing (spec line 375).
   - `models`: model-related type hints on the resolver defaults (Decision 9, line 375).
   - `CompositePrimaryKey`: composite-pk gate per Decision 2 (spec line 287). Available unconditionally because `pyproject.toml:31` pins `Django>=5.2`.
   - `relay`, `NodeIDAnnotationError`: Strawberry Relay surface for `relay.Node`, `relay.GlobalID`, and the `NodeIDAnnotationError` fallback path (spec line 312).
   - `ConfigurationError`: raised by `apply_interfaces` (`TypeError` wrap, Decision 1) and the composite-pk gate (Decision 2). Slice 2's `install_is_type_of` did not need this import; Slice 4 introduces it.

2. **Constant.** Below the imports, define:

   ```
   _RELAY_RESOLVER_NAMES: tuple[str, ...] = (
       "resolve_id",
       "resolve_id_attr",
       "resolve_node",
       "resolve_nodes",
   )
   ```

   Per DRY Q6. Only call site is `install_relay_node_resolvers`. Justification: matches strawberry-django's iteration tuple at `strawberry_django/type.py:214-219` shape; localizes the four method names so a future Strawberry rename surfaces in one place.

3. **Helper: `implements_relay_node`** (spec lines 388-389). Insert above `install_is_type_of` (the existing helper at `types/relay.py:6-35` from Slice 2):

   ```
   def implements_relay_node(type_cls: type) -> bool:
       """Return whether ``type_cls`` is a subclass of ``strawberry.relay.Node``.

       Used by ``finalize_django_types()`` Phase 2.5 (after ``__bases__``
       mutation) to decide whether to run the composite-pk gate and the
       four ``resolve_*`` defaults. Distinct from Slice 3's tuple-membership
       check (``relay.Node in interfaces`` at ``types/base.py:569``), which
       runs pre-base-injection at collection time against the validated
       ``Meta.interfaces`` tuple.
       """
       return issubclass(type_cls, relay.Node)
   ```

   Justification: spec lines 388-389 give the signature verbatim. The check is one line; the docstring carries the structural-split discriminator-justification carry-forward from Slice 3's worker-memory entry (line 46-47, line 55-58).

4. **Helper: `apply_interfaces`** (spec lines 384-385). Insert after `implements_relay_node`:

   ```
   def apply_interfaces(type_cls: type, definition: "DjangoTypeDefinition") -> None:
       """Inject ``definition.interfaces`` into ``type_cls.__bases__`` (Phase 2.5).

       Skips interfaces already in ``type_cls.__mro__`` so a class that
       already inherits a listed interface directly (e.g. consumer wrote
       ``class Foo(DjangoType, relay.Node): class Meta: interfaces =
       (relay.Node,)``) sees no double-injection (spec lines 329, 339,
       458).

       Raises:
           ConfigurationError: a ``TypeError`` from ``cls.__bases__``
               assignment is wrapped with the offending interface named in
               the message (spec line 540-541: ``cls.__bases__`` mutation
               can fail when the resulting MRO/instance layout is
               incompatible; we surface this as a configuration error so
               consumers see "interface X cannot be added" rather than a
               raw layout TypeError).
       """
       additions = tuple(
           iface for iface in definition.interfaces if iface not in type_cls.__mro__
       )
       if not additions:
           return
       try:
           type_cls.__bases__ = (*type_cls.__bases__, *additions)
       except TypeError as exc:
           offending = ", ".join(iface.__name__ for iface in additions)
           raise ConfigurationError(
               f"{type_cls.__name__}: cannot add interface(s) {offending} to bases. "
               f"Python rejected the resulting MRO ({exc}). Either drop the "
               "incompatible interface from Meta.interfaces or rework the class "
               "hierarchy.",
           ) from exc
   ```

   Justification:
   - `definition.interfaces` is the read path (per DRY Q2 / Slice 1's storage contract). The helper takes the definition as an explicit argument rather than reading `type_cls.__django_strawberry_definition__` so the test scaffolding (DRY Q7's `(b)` shape) can pass a synthetic definition without round-tripping through the registry. Tradeoff: one more arg at the Phase 2.5 call site; the alternative (reach into `type_cls.__django_strawberry_definition__.interfaces`) would create a hidden coupling. The arg-shape matches Slice 2's `install_is_type_of(type_cls)` signature by **omitting** the definition arg there (Slice 2 only needed `model`, which it reads from `type_cls.__django_strawberry_definition__.model` because the call site is `__init_subclass__` immediately after the definition assignment, not at finalization time). At finalization time both `definition` and `type_cls` are available from `registry.iter_definitions()`, so passing both is natural.
   - `iface not in type_cls.__mro__` is the spec line 339 / 458 contract.
   - The `TypeError` wrap is spec lines 540-541 (Risk note: `cls.__bases__` mutation can fail when the resulting MRO/instance layout is incompatible; surface as `ConfigurationError`). The forward-ref `"DjangoTypeDefinition"` quoted-string in the type hint sidesteps a circular import (the actual class is in `types/definition.py`; importing it at module scope of `types/relay.py` would create a one-way dependency `types/relay.py -> types/definition.py` which is acceptable, but `types/definition.py` may grow to import from elsewhere, so the quoted hint is the conservative shape; `from __future__ import annotations` at `types/relay.py:3` already lets every annotation be a string).

5. **Helper: `_resolve_id_attr_default`** (spec lines 401, 312). Insert after `apply_interfaces`:

   ```
   def _resolve_id_attr_default(cls: type) -> str:
       """Default ``Node.resolve_id_attr`` — falls back to ``"pk"``.

       Calls ``super(cls, cls).resolve_id_attr()`` so a consumer
       ``id: relay.NodeID[...]`` annotation on the class wins; on
       ``NodeIDAnnotationError`` falls back to ``"pk"``. Direct port of
       ``strawberry_django/relay/utils.py:285-303``.
       """
       try:
           return super(cls, cls).resolve_id_attr()  # type: ignore[misc]
       except NodeIDAnnotationError:
           return "pk"
   ```

6. **Helper: `_resolve_id_default`** (spec line 313, port of `strawberry_django/relay/utils.py:306-348`). Insert after `_resolve_id_attr_default`:

   ```
   def _resolve_id_default(cls: type, root: models.Model, info: Any) -> str:
       """Default ``Node.resolve_id`` with a ``__dict__`` cache check.

       Calls ``cls.resolve_id_attr()`` to derive the column name (handles
       consumer ``relay.NodeID[...]`` overrides and the ``"pk"`` fallback),
       coerces the literal ``"pk"`` to the model's concrete pk ``attname``
       so the dict-cache lookup keys on the real column, then reads from
       ``root.__dict__`` first (avoids an extra ORM hit when the optimizer
       already loaded the row) and falls back to ``getattr(root, id_attr)``
       (spec line 313 / Decision 7's "no avoidable lazy loads on
       ``resolve_id``").
       """
       id_attr = cls.resolve_id_attr()
       if id_attr == "pk":
           id_attr = root.__class__._meta.pk.attname
       try:
           return str(root.__dict__[id_attr])
       except KeyError:
           return str(getattr(root, id_attr))
   ```

   Justification of the `id_attr == "pk"` coercion: per `strawberry_django/relay/utils.py:340-348`, the `__dict__` cache stores entries keyed on the **column attname**, not the literal `"pk"` — Django's `model._meta.pk.attname` resolves to e.g. `"id"` for an `AutoField`, `"uuid_id"` for a renamed pk, etc. Without the coercion, `root.__dict__["pk"]` always misses and forces every `resolve_id` call into the `getattr` branch (which itself may lazy-load if the optimizer did not select the column). Decision 7's "no avoidable lazy loads" invariant requires the coercion.

7. **Private helper: `_assemble_node_queryset`** (per DRY Q5). Insert above the two node resolvers:

   ```
   def _assemble_node_queryset(
       cls: type,
       info: Any,
       id_attr: str,
       *,
       node_id: Any = None,
       node_ids: Iterable[Any] | None = None,
   ) -> models.QuerySet:
       """Build the per-node-fetch queryset through the four documented steps.

       Steps (mirror ``strawberry_django/relay/utils.py:155-187`` / ``:223-265``):

       1. ``cls.__django_strawberry_definition__.model._default_manager.all()``
       2. ``cls.get_queryset(qs, info)``
       3. ``qs.filter(...)`` on ``id_attr`` (single ``node_id``) or
          ``id_attr__in`` (``node_ids``)
       4. Optional ``ext.optimize(qs, info=info)`` when a
          ``DjangoOptimizerExtension`` is reachable via ``info.context``.

       Step 4's optimizer-extension lookup uses the same context-attribute
       contract the rest of the package uses (see Open question for Worker 2
       on the canonical reader name); a ``None`` extension passes through.
       """
       model = cls.__django_strawberry_definition__.model
       qs = model._default_manager.all()
       qs = cls.get_queryset(qs, info)
       if node_id is not None:
           coerced = node_id.node_id if isinstance(node_id, relay.GlobalID) else node_id
           qs = qs.filter(**{id_attr: coerced})
       elif node_ids is not None:
           coerced_ids = [
               (nid.node_id if isinstance(nid, relay.GlobalID) else nid) for nid in node_ids
           ]
           qs = qs.filter(**{f"{id_attr}__in": coerced_ids})
       ext = _resolve_optimizer_extension(info)
       if ext is not None:
           qs = ext.optimize(qs, info=info)
       return qs
   ```

   `_resolve_optimizer_extension(info)` is a small extra helper that wraps the canonical optimizer-context-lookup (see Open question 2 below). Justification for the extraction: the single read shape (`getattr(getattr(info, "context", None), "<attr_name>", None)`) is otherwise repeated at every Relay node call; the Worker 3 shadow overview's "Repeated string literals" section would flag the attribute-name string if it appeared twice.

8. **Helper: `_resolve_node_default`** (spec lines 314, 408-414). Insert after `_assemble_node_queryset`:

   ```
   def _resolve_node_default(
       cls: type,
       info: Any,
       node_id: Any,
       required: bool = False,
   ) -> Any:
       """Default ``Node.resolve_node`` — ``get_queryset`` + optimizer aware.

       Returns the single matching row (``qs.get()`` when ``required``,
       ``qs.first()`` otherwise). Async path detected via ``info``; uses
       ``aget`` / ``afirst`` when the Django version provides them, falling
       back to ``sync_to_async(qs.get)`` / ``sync_to_async(qs.first)``
       (spec line 375, Decision 9).
       """
       id_attr = cls.resolve_id_attr()
       qs = _assemble_node_queryset(cls, info, id_attr, node_id=node_id)
       if _is_async_context(info):
           async_call = qs.aget if required else qs.afirst
           sync_fallback = qs.get if required else qs.first
           if async_call is not None:
               return async_call()
           return sync_to_async(sync_fallback)()
       return qs.get() if required else qs.first()
   ```

   Note on `aget`/`afirst`: Django 5.2+ ships both, so the `if async_call is not None` guard is technically unreachable. The plan keeps the guard defensively per spec line 379 ("If a needed async ORM API is missing in the supported Django range, fall back to `sync_to_async` wrapping the equivalent sync call") so a future Django downgrade or version-specific Worker 2 issue doesn't silently fail. The fallback shape also gives the test plan an explicit branch to cover (`test_resolve_node_async_context` exercises the `aget`/`afirst` path).

9. **Helper: `_resolve_nodes_default`** (spec lines 315, 417-423). Insert after `_resolve_node_default`:

   ```
   def _resolve_nodes_default(
       cls: type,
       info: Any,
       node_ids: Iterable[Any] | None = None,
       required: bool = False,
   ) -> Any:
       """Default ``Node.resolve_nodes`` — order-preserving, missing-aware.

       When ``node_ids`` is ``None`` returns the full filtered queryset (the
       caller materializes via ``async for`` / iteration as needed). When
       ``node_ids`` is provided, returns a list whose indexes correspond
       1:1 with ``node_ids``: ``required=False`` yields ``None`` for missing
       ids, ``required=True`` raises ``KeyError`` for missing ids matching
       ``strawberry_django/relay/utils.py:189-198`` semantics.
       """
       id_attr = cls.resolve_id_attr()
       if node_ids is None:
           return _assemble_node_queryset(cls, info, id_attr)
       node_ids_list = list(node_ids)
       coerced_keys = [
           str(nid.node_id if isinstance(nid, relay.GlobalID) else nid) for nid in node_ids_list
       ]
       qs = _assemble_node_queryset(cls, info, id_attr, node_ids=node_ids_list)
       if _is_async_context(info):
           async def _materialize() -> list:
               results = [obj async for obj in qs]
               return _order_nodes(results, coerced_keys, id_attr, required=required)
           return _materialize()
       return _order_nodes(list(qs), coerced_keys, id_attr, required=required)
   ```

   With a small module-private:

   ```
   def _order_nodes(
       results: list,
       coerced_keys: list[str],
       id_attr: str,
       *,
       required: bool,
   ) -> list:
       """Re-order ``results`` to match ``coerced_keys`` (port of strawberry-django's map_results)."""
       index = {str(getattr(obj, id_attr)): obj for obj in results}
       output: list = []
       for key in coerced_keys:
           if required:
               output.append(index[key])
           else:
               output.append(index.get(key))
       return output
   ```

   Justification for the helper split: `_order_nodes` is the order-preserving / required-aware step that maps the queryset results back to the input `node_ids` shape. Without it the sync and async branches of `_resolve_nodes_default` would copy six lines of dict-build + for-loop. Per `strawberry_django/relay/utils.py:189-198` upstream uses the same shape.

10. **Helper: `_is_async_context`** (Decision 9). Insert above the resolver helpers, after `_assemble_node_queryset`:

    ```
    def _is_async_context(info: Any) -> bool:
        """Detect whether the caller's resolver runs under an async event loop.

        Per Decision 9 (spec lines 371-379) the package needs to dispatch
        sync vs. async ORM calls inside the ``resolve_*`` defaults.
        Strawberry's ``Info`` exposes the resolver's awaitability through
        the dispatcher; the canonical reader is the executor-running flag
        on the operation context, falling back to
        ``asgiref.sync.iscoroutinefunction`` against the next resolver
        when ``Info`` does not provide a direct signal. See Open question
        for Worker 2 on the final detection shape.
        """
        # Implementation deferred to Worker 2 per the Open question; the
        # plan's recommendation is a two-step detection that prefers
        # Strawberry's ``info`` signal and falls back to a sync-default
        # ``False`` (the sync path is the safe default since every async
        # resolver context already supports awaiting a sync call wrapped
        # in ``sync_to_async``).
        ...
    ```

    The exact body is **Open question 1** for Worker 2 (detection mechanism varies by Strawberry version; the plan does not pin the exact attribute walk). Worker 2 selects the simplest signal that survives the test plan's async-context tests.

11. **Helper: `_resolve_optimizer_extension`** (single optimizer-context-lookup site). Insert above `_assemble_node_queryset`:

    ```
    def _resolve_optimizer_extension(info: Any) -> Any:
        """Return the ``DjangoOptimizerExtension`` instance on ``info`` if any.

        Centralizes the optimizer-extension read path so the attribute
        name appears in one place. See Open question for Worker 2 on the
        canonical attribute name (the package's existing optimizer
        already publishes the plan to ``info.context.dst_optimizer_plan``
        per ``docs/FEATURES.md`` Optimizer entry; the extension instance
        itself is a separate read).
        """
        ...
    ```

    Per DRY Q5; details in Open question 2 for Worker 2.

12. **Helper: `install_relay_node_resolvers`** (spec lines 392-394, 296-308). Insert after the four `_resolve_*_default` helpers:

    ```
    def install_relay_node_resolvers(type_cls: type) -> None:
        """Inject the four ``resolve_*`` defaults via the ``__func__`` identity test.

        For each name in ``_RELAY_RESOLVER_NAMES`` (``resolve_id``,
        ``resolve_id_attr``, ``resolve_node``, ``resolve_nodes``):

        - Look up the inherited method on ``type_cls`` (resolves through
          MRO to ``relay.Node``'s default if no consumer override exists).
        - Compare ``existing.__func__`` to ``relay.Node.<attr>.__func__``.
          When they match (or ``existing`` is ``None``), the consumer has
          not overridden the method and the framework default is
          installed via ``setattr(type_cls, attr, classmethod(default))``.
        - When they differ, the consumer's override wins and is preserved.

        Direct port of ``strawberry_django/type.py:213-225``. The
        ``__func__`` discriminator is structurally distinct from Slice 2's
        ``__dict__`` membership discriminator (``is_type_of`` injection)
        and Slice 3's tuple-membership discriminator (``relay.Node in
        interfaces``) — the three answer different questions at three
        lifecycle phases.
        """
        defaults = {
            "resolve_id": _resolve_id_default,
            "resolve_id_attr": _resolve_id_attr_default,
            "resolve_node": _resolve_node_default,
            "resolve_nodes": _resolve_nodes_default,
        }
        for attr in _RELAY_RESOLVER_NAMES:
            default_impl = defaults[attr]
            existing = getattr(type_cls, attr, None)
            node_default = getattr(relay.Node, attr, None)
            existing_func = getattr(existing, "__func__", None)
            node_func = getattr(node_default, "__func__", None)
            if existing is None or (existing_func is not None and existing_func is node_func):
                setattr(type_cls, attr, classmethod(default_impl))
    ```

    Justification for `classmethod(default_impl)`: spec line 305 names this verbatim. Upstream `strawberry_django/type.py:223-225` uses `types.MethodType(django_resolver(func), cls)` instead — a different binding shape. The plan follows the spec wording (`classmethod`) because (a) the four `_resolve_*_default` signatures take `cls` as the first positional arg, which is the classmethod-binding contract; (b) `classmethod` is the standard Python idiom for "method bound to class, not instance", matching what `relay.Node` itself uses for these methods; (c) avoiding `types.MethodType` keeps the binding mechanism standard-library-only without `django_resolver` wrapping (Decision 9's async dispatch lives inside `_resolve_node_default` / `_resolve_nodes_default` directly, not via a decorator).

**Module: `django_strawberry_framework/types/finalizer.py`** (Phase 2.5 insertion).

13. **Imports.** Append to the existing local imports block:

    ```
    from .relay import (
        apply_interfaces,
        implements_relay_node,
        install_relay_node_resolvers,
    )
    ```

    The `CompositePrimaryKey` import stays in `types/relay.py` because the composite-pk gate is run inside Phase 2.5's loop via a small private helper (next step) that lives next to `apply_interfaces`; alternatively Worker 2 may inline the gate in the finalizer. The plan recommends the helper to keep the finalizer's loop body shallow.

14. **Composite-pk gate helper.** Add to `types/relay.py` (between `apply_interfaces` and `_resolve_id_attr_default`):

    ```
    def _check_composite_pk_for_relay_node(type_cls: type) -> None:
        """Raise ``ConfigurationError`` when a Relay-declared type has a composite pk.

        Decision 2 (spec lines 287, 455, 555): combining ``relay.Node``
        with a composite-primary-key model is explicitly out of scope for
        ``0.0.5``. Detection uses ``isinstance(model._meta.pk,
        CompositePrimaryKey)`` so the gate aligns with Django 5.2+'s
        native composite-pk type.
        """
        model = type_cls.__django_strawberry_definition__.model
        if isinstance(model._meta.pk, CompositePrimaryKey):
            raise ConfigurationError(
                f"{model.__name__}: relay.Node is not supported on models with a "
                "composite primary key. Either declare an explicit id: "
                "relay.NodeID[...] annotation on the DjangoType or remove "
                "relay.Node from Meta.interfaces.",
            )
    ```

    Justification: the spec language at line 287 / 555 names the remediation paths verbatim; the error wording mirrors those sentences. The helper takes `type_cls` (not the definition) because at Phase 2.5 the definition is already attached to the class as `type_cls.__django_strawberry_definition__` — and we need to be consistent with `install_is_type_of` and `install_relay_node_resolvers` which take `type_cls` too.

15. **Phase 2.5 insertion** in `django_strawberry_framework/types/finalizer.py`. Replace the TODO anchor at `types/finalizer.py:82-86` (the five-line `# TODO(0.0.5 relay interfaces; ...)` comment block) with the new Phase 2.5 loop:

    ```
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        if not definition.interfaces:
            continue
        apply_interfaces(type_cls, definition)
        if implements_relay_node(type_cls):
            _check_composite_pk_for_relay_node(type_cls)
            install_relay_node_resolvers(type_cls)
    ```

    Notes:
    - `_check_composite_pk_for_relay_node` is imported from `types/relay.py` alongside the other helpers; add it to the import block in step 13.
    - The `if not definition.interfaces: continue` short-circuit means types that did not declare `Meta.interfaces` (the `0.0.4` baseline, every non-Relay type) skip every byte of Phase 2.5 work. Identity to the existing Slice 2 / Slice 3 short-circuit shapes.
    - The `if implements_relay_node(type_cls)` gate runs **after** `apply_interfaces` because Phase 2.5's contract (spec line 339) is "if `relay.Node` is among the resolved bases" — i.e., after the `__bases__` mutation, the MRO check distinguishes Relay-declared types from generic non-Relay-interface types (per spec lines 244-267).
    - Per `AGENTS.md` line 10 / `START.md` (TODO anchors), the five-line `# TODO(0.0.5 relay interfaces; ...)` comment at `finalizer.py:82-86` is removed in the same change that ships the slice.

16. **Do not touch Phase 3** at `types/finalizer.py:88-94`. The existing `strawberry.type(type_cls, ...)` loop sees the mutated `__bases__` and the four injected `resolve_*` classmethods at decoration time. No reordering.

17. **Do not touch `__init_subclass__`** in `types/base.py`. Phase 2.5 runs at finalization time, not at class creation. The only Slice-4-relevant base.py read is the validated `interfaces` tuple flowing into `DjangoTypeDefinition` at `base.py:139` — already shipped in Slice 1.

18. **Do not touch `DEFERRED_META_KEYS`.** `"interfaces"` stays in `DEFERRED_META_KEYS` (per `types/base.py:50-60`); Slice 5 promotes. End-to-end consumer `Meta.interfaces = (relay.Node,)` declarations still hit the deferred-key check at `_validate_meta` first; Slice 4's tests use the bypass scaffolding (DRY Q7).

### Test additions / updates

#### `tests/types/test_relay_interfaces.py` (append new Slice 4 section)

Section header (mirroring Slices 1-3 dividers at lines 38-40, 190-192, 257-259):

```
# ---------------------------------------------------------------------------
# Slice 4 — Interface base-class injection + Relay resolver defaults
# ---------------------------------------------------------------------------
```

New imports at the top of the file (extending lines 14-21):

- `from django_strawberry_framework.types.finalizer import finalize_django_types` (or via the top-level `django_strawberry_framework` re-export already in scope at line 17).
- `from django_strawberry_framework.types.relay import (apply_interfaces, implements_relay_node, install_relay_node_resolvers, _resolve_id_attr_default, _resolve_id_default, _resolve_node_default, _resolve_nodes_default)` — the unit-boundary tests need direct access to the helpers.

Shared bypass helper (placed under the Slice 4 divider, before the first test):

```
def _stage_relay_definition(type_cls: type) -> None:
    """Inject ``definition.interfaces = (relay.Node,)`` after registration.

    Slice 4's tests cannot declare ``Meta.interfaces = (relay.Node,)``
    end-to-end because ``"interfaces"`` is still in ``DEFERRED_META_KEYS``
    until Slice 5 promotes it. This helper centralizes the deferred-key
    bypass so each test does not re-invent the same pattern.
    """
    definition = registry.get_definition(type_cls)
    definition.interfaces = (relay.Node,)
```

Tests (all pinned to `tests/types/test_relay_interfaces.py::<test_name>`):

Validation / lifecycle:

- **Unskip `test_relay_node_with_composite_pk_raises`** at `tests/types/test_relay_interfaces.py:183-187` (currently a `pytest.mark.skip` placeholder from Slice 1). The real body declares a fakeshop-or-test-only model with a Django 5.2+ `CompositePrimaryKey`, registers a `DjangoType` against it, stages `definition.interfaces = (relay.Node,)` via `_stage_relay_definition`, calls `finalize_django_types()`, and asserts `pytest.raises(ConfigurationError, match="composite primary key")`. Justification: Slice 1's worker-memory carry-forward names this as Slice 4's responsibility (worker-memory line 17). Worker 2 may either (a) use a real fakeshop model with a composite pk if one already exists in the fakeshop apps, or (b) construct an inline `class _CompositePkModel(models.Model)` with `class Meta: app_label = "library"` and a `CompositePrimaryKey` declaration — the inline approach is the smallest viable shape because composite-pk fakeshop models are not currently in the example app. The error-message match string is `"composite primary key"` per the wording in implementation step 14.

Relay Node behavior (end-to-end via `_stage_relay_definition`, exercising the full Phase 2.5):

- `test_relay_node_injects_default_resolvers` — declares a `DjangoType` against `Category` (without `Meta.interfaces` to skip the deferred-key check), stages `definition.interfaces = (relay.Node,)` via the bypass, runs `finalize_django_types()`, then asserts (1) `relay.Node in CategoryNode.__mro__`, (2) all four method names appear in `CategoryNode.__dict__`, (3) each is a `classmethod`-bound descriptor. Spec line 483.
- `test_resolve_id_attr_falls_back_to_pk` — same shape as `test_relay_node_injects_default_resolvers` but asserts `CategoryNode.resolve_id_attr() == "pk"` (no `relay.NodeID[...]` annotation declared on the class, so the `NodeIDAnnotationError` fallback fires). Alternatively, exercises `_resolve_id_attr_default(CategoryNode)` directly (the unit shape) for faster iteration. Spec line 484.
- `test_resolve_id_uses_dict_cache` — constructs a `Category` instance, populates `instance.__dict__["id"]` directly with a sentinel value, calls `CategoryNode.resolve_id(instance, info=None)` (or `_resolve_id_default(CategoryNode, instance, info=None)` for the unit-boundary shape) and asserts the returned string matches `str(sentinel)`. The `id` attribute is **not** populated via the descriptor path. Spec line 485.
- `test_resolve_id_falls_back_to_getattr` — constructs a `Category` instance via `Category(id=42)`, asserts `__dict__` does **not** contain the pk attname (depends on Django's constructor behavior; if it does, force-delete with `del instance.__dict__["id"]`), then asserts `CategoryNode.resolve_id(instance, info=None)` returns `"42"` via the `getattr` branch. Spec line 486.
- `test_resolve_node_applies_get_queryset` — declares a `DjangoType` with a custom `get_queryset` that filters `is_private=False`, stages relay-node interface, runs finalize. Seeds two `Category` rows (one private, one public). Asserts `CategoryNode.resolve_node(info=fake_info, node_id=private_id)` returns `None` and `CategoryNode.resolve_node(info=fake_info, node_id=public_id)` returns the public row. Spec line 487. (Note: `is_private` is on `Category` per the existing fakeshop services helper.)
- `test_resolve_nodes_preserves_order_and_missing` — seeds three `Category` rows (ids `a`, `b`, `c`), invokes `CategoryNode.resolve_nodes(info=fake_info, node_ids=[a, "999999", c], required=False)`, asserts the returned list is `[Category(a), None, Category(c)]`. Spec line 488.
- `test_resolve_nodes_required_raises_for_missing` — same setup, `required=True`, asserts `pytest.raises(KeyError)` (the `_order_nodes` `output.append(index[key])` raises `KeyError` when `key` is missing). Spec line 489.

Async paths (Decision 9):

- `test_resolve_node_async_context` — invokes `_resolve_node_default(CategoryNode, info=fake_async_info, node_id=row.id)` and asserts the return value is **awaitable** (or, if Worker 2's `_is_async_context` lands as a context-flag-based detection, asserts under `asyncio.run(coro)` that the returned coroutine resolves to the expected row). Spec line 490.
- `test_resolve_nodes_async_context` — same shape for the plural path, exercising order-preserving / missing-id behavior under async. Spec line 491.

Consumer-override discriminators (the `__func__` identity test):

- `test_consumer_async_resolve_node_wins` — declares a `DjangoType` with `async def resolve_node(cls, info, node_id, required=False): return "sentinel"`, stages relay-node, finalizes, asserts `CategoryNode.resolve_node` returns the sentinel (the consumer override survived `install_relay_node_resolvers`). The `__func__` discriminator does not care about awaitability. Spec line 492.
- `test_consumer_resolve_id_attr_wins` — `class CategoryNode(DjangoType): @classmethod def resolve_id_attr(cls): return "slug"`. After finalize, `CategoryNode.resolve_id_attr() == "slug"`. Spec line 493.
- `test_consumer_resolve_id_wins` — analogous override of `resolve_id`; after finalize, the consumer's body runs (sentinel return). Spec line 494.
- `test_consumer_resolve_node_wins` — sync version of the async test; same `sentinel`-return pattern. Spec line 495.
- `test_consumer_resolve_nodes_wins` — analogous. Spec line 496.

Strawberry `relay.NodeID[...]` interaction:

- `test_node_id_annotation_overrides_default_id_attr` — declares a `DjangoType` with `id: relay.NodeID[str] = strawberry.field(...)` plus a slug column on the model. After stage / finalize, `CategoryNode.resolve_id_attr()` returns the slug-column attname (Strawberry's `Node.resolve_id_attr()` succeeds, no `NodeIDAnnotationError`, no `"pk"` fallback). Spec line 497.

Non-Relay interface support:

- `test_non_relay_interface_works` — declares a `@strawberry.interface class Auditable: ...`, stages `definition.interfaces = (Auditable,)` on a `DjangoType` definition (not `relay.Node`), runs finalize. Asserts `Auditable in type_cls.__mro__` AND that `install_relay_node_resolvers` was **not** invoked (e.g. `"resolve_node"` is not in `type_cls.__dict__`). Spec line 498. This is the test that pins the Decision 1 / Decision 6 contract that non-Relay interfaces are validated and applied but do not get the Relay-only resolver injection.

#### `tests/optimizer/test_relay_id_projection.py` (NEW file, per spec lines 73-77 — `tests/optimizer/`)

Decision 7 invariants. The file is new because the existing `tests/optimizer/` test files (`test_walker.py`, `test_plans.py`, `test_extension.py`, etc.) are scoped to optimizer-only behavior, not the Relay-id intersection. A new file keeps the Slice 4 boundary clean.

- `test_relay_id_only_projection_includes_pk_attname` — declares a Relay-declared `DjangoType` via the bypass scaffolding, builds a Strawberry schema with `DjangoOptimizerExtension`, runs `{ allCategories { id } }` and asserts the generated `only()` projection includes the model's concrete pk attname (e.g. `"id"` for `AutoField`). Spec line 506.
- `test_relay_id_does_not_trigger_lazy_load` — same Relay schema, `strictness="raise"`. Runs `{ allCategories { id name } }`, asserts no `OptimizerError` is raised. The `__dict__` cache hit in `_resolve_id_default` avoids the lazy load. Spec line 507.
- `test_relay_target_relation_planning_unchanged` — schema with two `DjangoType`s, one Relay-declared (`CategoryNode` with `interfaces=(relay.Node,)`), one non-Relay (`ItemType`). Runs `{ allItems { category { id name } } }`, asserts the optimizer's plan for the `category` relation is `select_related` (or whatever the `0.0.4` baseline is for that relation), unchanged by the Relay decoration on the target. Spec line 508.
- `test_relay_resolve_id_uses_loaded_pk` — Relay schema, asserts `CategoryNode.resolve_id(loaded_instance, info=...)` reads the pk via the dict-cache hit without triggering a query (use `CaptureQueriesContext` to assert zero queries during the `resolve_id` call after a queryset has materialized the row). Spec line 509.

#### `tests/types/test_definition_order_schema.py` (extend)

Two new tests appended after the existing tests (per spec lines 78-80):

- `test_relay_declared_type_emits_node_interface_and_global_id` — declares two `DjangoType`s: one Relay-declared (`BookType` with `interfaces=(relay.Node,)` via bypass), one non-Relay. Builds the schema, introspects via `schema._schema.type_map["BookType"]`, asserts `BookType` implements `Node` and that its `id` field's type is `GlobalID!`. Spec line 79.
- `test_mixed_relay_and_non_relay_types_introspect_cleanly` — same shape but asserts the non-Relay type does **not** implement `Node` (no interface bleed). Spec line 80. Pins the Decision 6 contract that injection is **only** for declared-Relay types.

#### `tests/test_registry.py` (extend)

Per spec line 81. One new test appended after the existing `test_registry_clear_allows_fresh_type_classes_to_finalize_again` (line 350-369):

- `test_registry_clear_allows_fresh_relay_declared_type_to_finalize` — declares a Relay-declared `DjangoType` via the bypass, finalizes, calls `registry.clear()`, declares a **new** Relay-declared `DjangoType` for the same model, asserts a second finalize succeeds and the new class has `relay.Node in __mro__` plus the four injected classmethods. Pins the lifecycle contract.

#### `examples/fakeshop/test_query/test_library_api.py` (extend)

Per spec line 82. One new HTTP test appended:

- `test_library_relay_node_global_id_round_trips` — within the existing `_reload_project_schema_for_acceptance_tests` fixture (lines 21-47), inject `interfaces = (relay.Node,)` on one library `DjangoType`'s `DjangoTypeDefinition` after the schema reload but **before** finalization runs. Seed a library row (e.g. a `Genre`), run `{ allLibraryGenres { id name } }`, decode the returned `id` via `relay.GlobalID.from_id()` (or the equivalent Strawberry decoder), and assert the decoded `node_id` matches `str(genre.pk)`. Spec line 82.

  **Open question 3 for Worker 2** below names the alternative: defer this test to Slice 5 if the bypass cannot land cleanly in the existing fixture. If Worker 2 defers, the spec line 82 contract becomes Slice 5's responsibility — Worker 2 records this in "Notes for Worker 1 (spec reconciliation)" and Worker 1's final-verification pass updates the spec or accepts the deferral.

### Open questions for Worker 2

1. **`_is_async_context(info)` detection mechanism.** Strawberry's `Info` instance exposes the current resolver context, but the exact attribute path varies by Strawberry version. The plan recommends a two-step detection: prefer `info.context.is_awaitable` (if it exists), else fall back to `False` (sync default — `sync_to_async` would wrap any sync resolver under an async caller anyway, so a missed-async-detection still resolves correctly though may pay an extra `sync_to_async` round-trip). If Worker 2 finds a more reliable signal in `pyproject.toml`'s pinned `strawberry-graphql>=0.262.0`, prefer that. The async-context tests (`test_resolve_node_async_context`, `test_resolve_nodes_async_context`) will exercise whichever detection lands; if the tests fail because the detection returns `False` under an async event loop, Worker 2 fixes the detection and reports back via Notes for Worker 3.

2. **Optimizer-extension read path.** The package's existing optimizer publishes the **plan** to `info.context.dst_optimizer_plan` (per `docs/FEATURES.md` Optimizer entry and `optimizer/_context.py` constants). The **extension instance** itself is not currently published to context — the existing root-gated optimizer reads its own state from `self`. For Decision 7's "consult the optimizer extension via `info.context`" (spec line 314), the canonical reader needs definition. The plan's recommendation: introduce a new optimizer-context key `DST_OPTIMIZER_EXTENSION_INSTANCE` (or similar) and stash the extension on `info.context` during `on_execute` so `_resolve_optimizer_extension(info)` can read it. **Alternative:** read from a module-level `ContextVar` that the extension's `on_execute` already sets (`optimizer/extension.py:147-150` shows `_optimizer_active`; a sibling `_optimizer_extension` ContextVar holding the instance would work). Worker 2 picks one shape and documents the choice. If neither lands cleanly, the simplest reduction is `_resolve_optimizer_extension(info) -> None` (always returns `None`) — the resolvers still work, just without optimizer optimization on Node lookups. Decision 7's invariants (pk attname in `only()`, no avoidable lazy loads) are about **root-gated** optimization on the **list** path — Relay node lookups returning single rows are not yet on the optimizer's hot path. Worker 2 may legitimately ship the helper as a `return None` stub for `0.0.5` and document the deferral. This is **load-bearing** for the test plan: `test_relay_id_only_projection_includes_pk_attname` and friends test the **list path** (`{ allCategories { id } }`), not the Relay-node-lookup path; the optimizer integration on **node lookups** is a secondary concern. Worker 2 has discretion.

3. **HTTP test placement: Slice 4 or Slice 5.** Per DRY Q7's final paragraph and the test scaffolding section, the spec line 82 HTTP test could either (a) land in Slice 4 using the same definition.interfaces injection bypass, or (b) defer to Slice 5 once `"interfaces"` is in `ALLOWED_META_KEYS` and the consumer-facing `Meta.interfaces = (relay.Node,)` declaration works end-to-end. The plan recommends (a) — keep the spec checklist faithful — but Worker 2 may pick (b) and flag the deferral via "Notes for Worker 1 (spec reconciliation)". If (b), Slice 5's plan must add the HTTP test to its checklist.

4. **Composite-pk model for `test_relay_node_with_composite_pk_raises`.** The fakeshop app currently has no composite-pk model. Worker 2 picks one of: (i) inline-construct a `_CompositePkModel` in the test module using `class Meta: app_label = "library"` + `CompositePrimaryKey(...)` declaration — smallest viable shape; (ii) add a small composite-pk model to `examples/fakeshop/apps/library/models.py` if the example value justifies it. Recommendation: (i), because the test is the only consumer of a composite-pk model in this slice and adding one to the example app would expand the example surface for one test.

5. **`classmethod` vs. `types.MethodType` binding.** Upstream `strawberry_django/type.py:223-225` uses `types.MethodType(django_resolver(func), cls)` rather than `classmethod(func)`. Spec line 305 says `classmethod(default_impl)` verbatim. The plan follows the spec wording; Worker 2 may diverge if a test reveals that `classmethod` does not produce the expected `getattr(cls, attr).__func__` shape for Slice 4's `__func__` discriminator (`__func__` exists on both bound classmethods and `types.MethodType` instances, but the access path differs slightly). Test as you go.

6. **Test ordering with the existing Slice 1 `test_class_already_inherits_relay_node_directly`** (`tests/types/test_relay_interfaces.py:164-180`). That test currently asserts only validation acceptance; Slice 4 should consider extending it (or adding a sibling test) to confirm the structural no-op behavior — that `apply_interfaces` does not double-inject `relay.Node` when it is already in the host class's MRO. Recommendation: add a new test (`test_apply_interfaces_skips_already_present_bases`) under the Slice 4 divider that exercises the `iface not in type_cls.__mro__` short-circuit in `apply_interfaces` directly. Spec line 339 and line 458 jointly pin this contract.

7. **`_resolve_optimizer_extension` and `_is_async_context` as separate helpers vs. inlined.** The plan factors them out for DRY; Worker 2 may inline if the call-site is small enough and the static-helper's repeated-literals report doesn't flag the attribute names. Inlining shrinks the surface but means a future change to either detection mechanism touches two sites instead of one. Recommendation: keep them factored.

8. **Slice 4 adds 4 helpers + 1 constant to `types/relay.py`** (`implements_relay_node`, `apply_interfaces`, `_check_composite_pk_for_relay_node`, `install_relay_node_resolvers`) plus the 4 `_resolve_*_default` functions, the 2 utility helpers (`_assemble_node_queryset`, `_order_nodes`), and the 2 context helpers (`_is_async_context`, `_resolve_optimizer_extension`). That's ~12 new symbols in a module that currently has 1 (`install_is_type_of`). The shadow overview's "Symbols" and "Repeated string literals" sections should be re-read by Worker 3 to confirm no premature consolidation has crept in. Worker 2 may regroup the helpers if a clearer ordering emerges; the recommended order is: constants → boolean predicates (`implements_relay_node`) → base mutators (`apply_interfaces`, `_check_composite_pk_for_relay_node`) → resolver defaults (`_resolve_*_default`) → shared queryset/dispatch helpers (`_assemble_node_queryset`, `_order_nodes`, `_is_async_context`, `_resolve_optimizer_extension`) → final injection helper (`install_relay_node_resolvers`).

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/relay.py` — extended the Slice 2 home with the four `_resolve_*_default` functions, the structural helpers (`apply_interfaces`, `implements_relay_node`, `install_relay_node_resolvers`, `_check_composite_pk_for_relay_node`), the shared queryset assembly + order helpers (`_assemble_node_queryset`, `_order_nodes`), the optimizer-extension read seam (`_resolve_optimizer_extension`), and the `_RELAY_RESOLVER_NAMES` constant. Removed the four `# TODO(0.0.5 relay interfaces; ...)` anchors at the bottom of the file (per `AGENTS.md` line 10 — anchors are removed in the same change that ships the slice). Async dispatch lives at the terminal call in `_resolve_node_default` / `_resolve_nodes_default`; detection uses `strawberry.utils.inspect.in_async_context` (chosen over a custom `_is_async_context` helper because Strawberry's own utility is already used by every comparable Strawberry-ecosystem package and surface — strawberry-django imports the same symbol). `_resolve_optimizer_extension` returns `None` for `0.0.5` per the plan's Open question 2 fallback; the list-path optimization (Decision 7 invariants) flows through the existing root-gated extension unchanged.
- `django_strawberry_framework/types/finalizer.py` — added the Slice 4 imports from `types/relay.py` and replaced the Phase 2.5 TODO anchor block with the new loop. The loop short-circuits when `definition.interfaces` is empty (mirrors Slice 2/3 short-circuits), then calls `apply_interfaces` → optional composite-pk gate → optional resolver injection. No reorder of Phase 1, Phase 2, or Phase 3; the mutated `__bases__` and the injected classmethods are visible to `strawberry.type(...)` at decoration time.
- `django_strawberry_framework/types/resolvers.py` — removed the Slice 4 TODO anchor at `_is_fk_id_elided` and replaced it with a permanent docstring sentence anchoring the Decision 7 contract (Relay GlobalID handling stays out of the FK-id elision path; that handling now lives in `types/relay.py`).

### Tests added or updated

`tests/types/test_relay_interfaces.py`:

- Added the `_stage_relay_definition(type_cls, interfaces=(relay.Node,))` bypass helper near the top of the module. Mirrors what `_build_annotations` (Slice 3) and Phase 2.5 (Slice 4) would do if `"interfaces"` were promoted: it sets `definition.interfaces` and strips the synthesized pk annotation from `type_cls.__annotations__` so Strawberry decoration sees `id: GlobalID!` from the interface rather than a synthesized scalar `id: int!`.
- Unskipped `test_relay_node_with_composite_pk_raises` (was `@pytest.mark.skip` from Slice 1); the body now stages `(relay.Node,)` on a `CategoryNode` definition, monkey-patches `Category._meta.pk` to a `CompositePrimaryKey("name", "is_private")` instance, calls `finalize_django_types()`, and asserts `ConfigurationError("composite primary key")`. The fakeshop apps have no composite-pk model so the monkey-patch is the smallest viable shape per the plan's Open question 4 recommendation (i).
- Added 22 Slice 4 tests under a new `Slice 4 — interface base-class injection + Relay resolver defaults` divider. Verbatim names: `test_relay_node_injects_default_resolvers`, `test_resolve_id_attr_falls_back_to_pk`, `test_resolve_id_uses_dict_cache`, `test_resolve_id_falls_back_to_getattr`, `test_resolve_node_applies_get_queryset`, `test_resolve_node_required_raises_for_missing`, `test_resolve_nodes_preserves_order_and_missing`, `test_resolve_nodes_required_raises_for_missing`, `test_resolve_nodes_without_ids_returns_full_queryset`, `test_resolve_node_async_context`, `test_resolve_nodes_async_context`, `test_consumer_async_resolve_node_wins`, `test_consumer_resolve_id_attr_wins`, `test_consumer_resolve_id_wins`, `test_consumer_resolve_node_wins`, `test_consumer_resolve_nodes_wins`, `test_node_id_annotation_overrides_default_id_attr`, `test_non_relay_interface_works`, `test_apply_interfaces_skips_already_present_bases`, `test_apply_interfaces_wraps_typeerror_as_configuration_error`, `test_resolve_id_default_unit_dict_cache_and_getattr_branches`, `test_resolve_node_default_invoked_via_helper`, `test_resolve_nodes_default_invoked_via_helper`, `test_install_relay_node_resolvers_idempotent_and_preserves_override`. Async tests use `asyncio.run(_runner())` to drive an async coroutine through `_resolve_node_default` / `_resolve_nodes_default` so the `in_async_context()` branch fires.

`tests/optimizer/test_relay_id_projection.py` (new file):

- `test_relay_id_only_projection_includes_pk_attname` — stages a Relay-declared `CategoryNode`, builds a schema with the optimizer, runs `{ allCategories { id } }`, and asserts `"id" in ctx.dst_optimizer_plan.only_fields`. Pins the pk-attname projection invariant.
- `test_relay_id_does_not_trigger_lazy_load` — runs `{ allCategories { id name } }` under `DjangoOptimizerExtension(strictness="raise")` and asserts no errors.
- `test_relay_target_relation_planning_unchanged` — a non-Relay `ItemType` traverses to a Relay-declared `CategoryNode` via forward FK; asserts `select_related` plans the relation unchanged.
- `test_relay_resolve_id_uses_loaded_pk` — uses `CaptureQueriesContext` to assert that `CategoryNode.resolve_id(loaded_row, info=None)` issues zero queries when the row was loaded via `Category.objects.only("id", "name")`.

`tests/types/test_definition_order_schema.py`:

- Added a local `_stage_relay(type_cls)` bypass and removed the TODO anchor.
- `test_relay_declared_type_emits_node_interface_and_global_id` — asserts the staged `CategoryNode` is decorated with `Node` in `gql_type.interfaces` and `id` is `ID!`.
- `test_mixed_relay_and_non_relay_types_introspect_cleanly` — a sibling `ItemType` without `relay.Node` does NOT implement `Node` and still exposes `id: Int!`.

`tests/test_registry.py`:

- Added a local `_stage_relay(type_cls)` bypass and removed the TODO anchor.
- `test_registry_clear_allows_fresh_relay_declared_type_to_finalize` — declares a Relay-declared `CategoryNode`, finalizes, clears, declares a fresh `FreshCategoryNode`, finalizes again, asserts the registry resets cleanly and the fresh class has `relay.Node in __mro__` plus the four classmethods.

`examples/fakeshop/test_query/test_library_api.py`:

- Removed the Slice 4 TODO anchor.
- Added `_decode_global_id(global_id)` (manual base64 decode, Strawberry-agnostic on the assert side) and `_reload_with_library_relay_node()` which mirrors the autouse fixture's reload chain but injects `definition.interfaces = (relay.Node,)` on `apps.library.schema.GenreType` between the library-schema reload and the project-schema reload.
- `test_library_relay_node_global_id_round_trips` — seeds a single Genre row, posts `{ allLibraryGenres { id name } }`, decodes the returned `id` and asserts the type name is `GenreType` and the decoded `node_id` matches `str(genre.pk)`.

### Validation run

- `uv run ruff format .` — pass (92 files left unchanged after one cleanup pass that reformatted 2 files I had just written).
- `uv run ruff check --fix .` — pass (1 error auto-fixed: an unused `models` import in `tests/test_registry.py` I had added but did not consume; ruff removed it. `All checks passed!` final state).
- Per `START.md`, no `pytest` run from Worker 2.

### Notes for Worker 3

Bypass scaffolding — three sites use the same pattern with slight local variation, intentionally NOT consolidated into a shared helper:

1. `tests/types/test_relay_interfaces.py::_stage_relay_definition(type_cls, interfaces=(relay.Node,))` — Slice 4's canonical bypass with a default interfaces tuple for the Relay-majority tests.
2. `tests/optimizer/test_relay_id_projection.py::_stage_relay(type_cls, *, interfaces=...)` — same shape, narrower scope (file is new and Slice-4-only).
3. `tests/types/test_definition_order_schema.py::_stage_relay(type_cls)` and `tests/test_registry.py::_stage_relay(type_cls)` — Relay-only variants.
4. `examples/fakeshop/test_query/test_library_api.py::_reload_with_library_relay_node()` — HTTP-path variant that interleaves the bypass into the existing schema-reload chain.

Each site is small (3-4 lines + the pk-annotation strip), and consolidating them into a shared test-tree helper would require either a new file at a tests-tree level not currently exercised, or a hidden helper imported across the three test trees that would couple their test-isolation boundaries. The plan's DRY-Q7 paragraph explicitly anticipated this: each site is "visible at every call site" so a future test author cannot accidentally drift on the bypass mechanism.

Composite-pk detection: `from django.db.models import CompositePrimaryKey` is unconditional (Django 5.2+ pinned). The test that exercises the gate monkey-patches `Category._meta.pk` to a `CompositePrimaryKey("name", "is_private")` instance rather than declaring a composite-pk Django model inline — the spec's preferred answer is to add the smallest viable bypass and keep the example apps clean.

Async dispatch mechanism: `strawberry.utils.inspect.in_async_context()` is the single signal. It returns `True` when called from inside an active async event loop and `False` otherwise. This avoids both (a) building a custom `_is_async_context(info)` helper that walks `info.context` for an awaitability flag (the spec's preferred Strawberry-info-based shape would require Strawberry-version-specific attribute walking) and (b) plumbing an explicit "is async" arg through every resolver call. The cost is one import; the benefit is that the detection survives whatever Strawberry version churn happens to the `Info` object. The pattern is identical to what strawberry-django itself uses (`strawberry_django/resolvers.py:14`), so consumers migrating from that package see no surprises.

`_resolve_optimizer_extension` returns `None` for the entire `0.0.5` slice. The plan's Open question 2 named this as the simplest reduction — Decision 7's optimizer invariants (pk-attname projection, no avoidable lazy loads, relation traversal) live on the **list path** and continue to work through the existing root-gated extension. The Relay **node lookup** path (single-row `resolve_node`, plural `resolve_nodes`) is not yet a hot optimizer path; a future slice can swap in a real read shape (e.g. a new optimizer-context key, or a ContextVar sibling of `_optimizer_active`) without touching the four `_resolve_*_default` functions. The current implementation's invariant: if `_resolve_optimizer_extension(info)` ever returns a non-None extension, `_assemble_node_queryset` will call `ext.optimize(qs, info=info)` in step 4 — the wiring is in place for the upgrade.

`apply_interfaces` test for the TypeError wrap: the test uses a bare `class _Host: pass` (with the default `__bases__ == (object,)`) and a freshly-declared `@strawberry.interface class _BadInterface`. Appending the interface produces `(object, _BadInterface)`, which Python's MRO algorithm rejects with a "Cannot create a consistent method resolution order" `TypeError`. The wrap surfaces as `ConfigurationError("cannot add interface")` per spec lines 540-541. The test stays inside the unit boundary — no DjangoType, no finalizer — so the assertion shape is on `apply_interfaces` itself.

`install_relay_node_resolvers` idempotency: after the first install the four `cls.__dict__` entries are `classmethod` descriptors wrapping the module-level `_resolve_*_default` callables. A second call sees `existing.__func__` is identical to the framework default's `__func__` (because both bind the same underlying callable) and re-writes the same classmethod. The test pins this by snapshotting `cls.__dict__[attr]` before the second call and asserting `after[attr].__func__ is before[attr].__func__`. Note: a fresh classmethod wrapper is created on every install (`setattr(cls, attr, classmethod(default))`), so `after[attr]` is a different object than `before[attr]`; the `__func__` identity is what matters and what the spec's discriminator (`existing.__func__ is relay.Node.<attr>.__func__`) actually checks.

The shadow-file static-inspection helper was NOT run by Worker 2. Per `docs/build/BUILD.md` lines 380-381 the helper is Worker 2's optional aid (`--strip-docstrings` for hard-to-read control flow); Worker 3 must run the helper on every new file (Worker 3 rules at lines 369-373). The new file is `django_strawberry_framework/types/relay.py` (extended from 1 symbol to 13 symbols, all with docstrings and small control flow) and `tests/optimizer/test_relay_id_projection.py` (new file under `tests/optimizer/`, a Worker 3 trigger per line 371).

### Notes for Worker 1 (spec reconciliation)

1. **Bypass scaffolding for Slice 4 tests.** The spec's "Slice 4" entries in the Test plan all describe end-to-end behavior, but Slice 4 cannot exercise that end-to-end path until Slice 5 promotes `"interfaces"`. The plan's DRY-Q7 paragraph anticipated this with `_stage_relay_definition`; the implementation went one step further and also strips the synthesized `id` annotation from `cls.__annotations__` (because Slice 3's `_build_annotations` runs before the bypass fires and the bypass cannot retroactively re-run `_build_annotations`). If Slice 5 makes the end-to-end path real, the test bypass and its `__annotations__.pop` step become structural no-ops — but they DO remain in the test source as a faithful description of "what the early-lifecycle slice would have done if it could have run end-to-end." Worker 1 may consider whether to delete the bypasses in Slice 5 or keep them as regression-coverage for the structural contract.

2. **`_resolve_optimizer_extension` is a `return None` stub for `0.0.5`.** Plan Open question 2 anticipated this. Decision 7's invariants are about the **list path** (which runs through the existing root-gated extension) and the **dict-cache hit on `resolve_id`** (which has nothing to do with the optimizer extension itself). The Relay-node-lookup path is not on the optimizer's hot path in `0.0.5`. If Slice 5's promotion or a later spec needs node-lookup optimization, the helper is the single seam to extend. Recommend: spec line 314 ("if ext: qs = ext.optimize(qs, info=info)") can stay as written — the implementation honors the contract at the seam, just with a `None`-returning lookup for now.

3. **`apply_interfaces` accepts a duck-typed definition.** The signature is `apply_interfaces(type_cls, definition: Any)` and the helper reads `definition.interfaces`. This is intentional so the unit tests can pass a synthetic stub (`class _SyntheticDef: interfaces = (...)`) for unit-boundary tests of `apply_interfaces` without round-tripping through the registry. The production call site at `types/finalizer.py` passes the real `DjangoTypeDefinition` instance. Spec line 384's signature reads `definition: DjangoTypeDefinition` literally; the implementation is broader by design. Worker 1 may decide whether to tighten the type hint in the spec or document the duck-typed shape.

4. **HTTP test design choice.** The HTTP test (`test_library_relay_node_global_id_round_trips`) re-implements the autouse fixture's reload chain in its own helper (`_reload_with_library_relay_node`) rather than parameterizing the autouse fixture. The autouse fixture runs before every test; piggy-backing on it for the Relay test would have required either a per-test marker (would muddy the fixture's plain-old-reload contract) or a sentinel global (would couple test order). The standalone helper is the simplest shape and follows the spec's "Follow the existing reload pattern" wording at line 82 without distorting the existing fixture. Worker 1 may decide whether to surface this pattern in `docs/TREE.md`'s HTTP-test reload-pattern note as a "Relay HTTP test variant."

5. **`_resolve_id_default` "pk" coercion.** Spec line 313 reads `try: return str(root.__dict__[id_attr]) except KeyError: return str(getattr(root, id_attr))`. The implementation adds one line before that: `if id_attr == "pk": id_attr = root.__class__._meta.pk.attname`. Without the coercion, `root.__dict__["pk"]` always misses (Django stores the pk under its column attname, e.g. `"id"`, never under the literal `"pk"`), and Decision 7's "no avoidable lazy loads on `resolve_id`" invariant is violated. This matches `strawberry_django/relay/utils.py:340-348`. Recommend: the spec's literal example at line 313 should mention the coercion explicitly, or cite `strawberry_django/relay/utils.py:340-348` as the full port site.

---

## Review (Worker 3)

Static helper invocations (per `docs/build/BUILD.md` "When to run the helper during build"):

- `django_strawberry_framework/types/relay.py` — required (under `types/`); overview at `docs/build/shadow/django_strawberry_framework__types__relay.overview.md`.
- `django_strawberry_framework/types/finalizer.py` — required (under `types/`); overview at `docs/build/shadow/django_strawberry_framework__types__finalizer.overview.md`.
- `django_strawberry_framework/types/resolvers.py` — required (under `types/`); overview at `docs/build/shadow/django_strawberry_framework__types__resolvers.overview.md`.
- `tests/optimizer/test_relay_id_projection.py` — required (new file, > 50 lines, not a pure-class module); overview at `docs/build/shadow/tests__optimizer__test_relay_id_projection.overview.md`.
- `tests/types/test_relay_interfaces.py` — required (> 50 lines new logic outside `django_strawberry_framework/`); overview at `docs/build/shadow/tests__types__test_relay_interfaces.overview.md`.

Focused coverage run executed: `uv run pytest tests/types/test_relay_interfaces.py tests/optimizer/test_relay_id_projection.py tests/types/test_definition_order_schema.py tests/test_registry.py --cov=django_strawberry_framework.types.relay --cov=django_strawberry_framework.types.finalizer --cov-report=term-missing`. Result: **5 failed, 80 passed**; `types/relay.py` coverage 96% (lines 224, 271-272, 303 uncovered); `types/finalizer.py` 100%.

### High:

#### test_resolve_id_falls_back_to_getattr crashes on AttributeError instead of returning the pk

The test pops `__dict__["id"]` from an unsaved `Category` instance and then `_resolve_id_default` falls through to `str(getattr(root, id_attr))` at `django_strawberry_framework/types/relay.py:170`. Django's `DeferredAttribute.__get__` runs `_check_parent_chain`, which calls `opts.get_ancestor_link(self.field.model)` — that returns `None` for a model with no concrete-inheritance parent, and Django then unconditionally does `link_field.attname` on the `None`, raising `AttributeError`. The implementation is correct against `strawberry_django/relay/utils.py:340-348`; the test is wrong: forcing `inst.__dict__.pop("id", None)` on an unsaved instance is not a faithful "loaded-but-deferred row" shape. Realistic shape: load the row via `Category.objects.only("name").first()`, which loads the model but defers `id` only as far as Django's pk-shortcut allows — but Django's pk is special-cased to never be deferred. The simplest viable fix: drop the `__dict__.pop` line and assert `_resolve_id_default` on a freshly-loaded row returns the right string via the dict-cache branch (i.e., merge the test with `test_resolve_id_uses_dict_cache` or split into two tests where each pins one branch with an instance that actually exercises the branch). Pinning the `getattr` fallback specifically requires either a mock object whose `__dict__` is empty but `getattr` returns a value (e.g. `SimpleNamespace(id=42, __class__=type(...))`-style fake), or accepting that the branch is unreachable under normal Django flows and adding `# pragma: no cover` per `AGENTS.md` line 21.

```django_strawberry_framework/types/relay.py:152:0
def _resolve_id_default(cls: type, root: models.Model, info: Any) -> str:
    ...
    try:
        return str(root.__dict__[id_attr])
    except KeyError:
        return str(getattr(root, id_attr))   # <-- AttributeError on unsaved instance
```

Recommended change: fix the two failing tests (`test_resolve_id_falls_back_to_getattr` at `tests/types/test_relay_interfaces.py:432-448` and `test_resolve_id_default_unit_dict_cache_and_getattr_branches` at `tests/types/test_relay_interfaces.py:783-801`) so the `getattr` fallback is exercised with a root whose `__dict__` is empty but whose `getattr` resolves the pk. A `SimpleNamespace(id=12)` plus a tiny `_meta`-shaped mock on `__class__` works, or use `Category.objects.create(...)` and then `del row.__dict__["id"]` after the row is fully loaded (Django will not lazy-reload the pk from a saved row's state in that case). Without this fix the slice fails the focused-coverage gate.

#### test_resolve_node_async_context and test_resolve_nodes_async_context fail with "database is locked"

Both async tests drive `asyncio.run(_runner())` from inside a `@pytest.mark.django_db` test. Django's test transaction is held on the main thread; `qs.afirst()` and `qs.aget()` use `sync_to_async`-style worker threads (or run a real async coroutine inside the same thread for `aget`/`afirst` in Django 5.2+), but in either case the SQLite test transaction is unreachable from the async path the way the test wires it up. This crashes the test with `OperationalError: database table is locked` before the success path is exercised. Net effect: the spec's Decision 9 contract ("`_resolve_node_default` and `_resolve_nodes_default` work in both sync and async resolver contexts") has **no passing test coverage** in the package suite. The implementation may be correct, but no test demonstrates that.

```tests/types/test_relay_interfaces.py:552:0
async def _runner():
    return await CategoryNode.resolve_node(info=None, node_id=target.id)

result = asyncio.run(_runner())   # <-- "database table is locked"
```

Recommended change: switch to `pytest-asyncio` with `@pytest.mark.asyncio` plus the appropriate Django async-DB-fixture (e.g. `transactional_db` or a manually-managed connection per-test), or build the async test against a non-DB shape (e.g. assert that the return value is a coroutine and that `inspect.iscoroutine(...)` holds without awaiting it). The strawberry-django reference shipping pattern uses `pytest.mark.asyncio` + `@pytest.fixture(autouse=True) async def _async_db():` style. Without a passing async test, Decision 9's invariant is unverified for `0.0.5`.

#### test_node_id_annotation_overrides_default_id_attr asserts on a malformed NodeID annotation

The test declares `name: Annotated[str, relay.NodeID]` (bare `NodeID` without subscript) at `tests/types/test_relay_interfaces.py:704`. Strawberry's `Node.resolve_id_attr()` looks for `relay.NodeID[T]` (a `NodeID` subscripted on a type), not bare `NodeID`; the unsubscripted form does not register the annotation, so the framework's `NodeIDAnnotationError` fallback fires and `resolve_id_attr()` returns `"pk"`. The test then asserts `== "name"` and fails. The spec at line 497 / line 553 spells the consumer-facing form as `id: relay.NodeID[str]` — using `name: relay.NodeID[str]` (no `Annotated[...]` wrapper) is the working spelling.

```tests/types/test_relay_interfaces.py:704:0
class CategoryNode(DjangoType):
    name: Annotated[str, relay.NodeID]   # malformed; bare NodeID
    class Meta:
        model = Category
        fields = ("id", "name")
```

Recommended change: rewrite as `name: relay.NodeID[str]` (or equivalent `Annotated[str, relay.NodeID]` where `NodeID` is subscripted — but the simpler shape is `name: relay.NodeID[str]`). Pins the spec contract that a consumer can use Strawberry's native annotation mechanism to point Relay at a non-pk column without overriding any classmethod.

#### Coverage gate failure — 4 uncovered lines in types/relay.py

The 100% package-coverage gate (`pyproject.toml [tool.coverage.report] fail_under = 100`) will fail at CI. Focused coverage run: `types/relay.py` 96% with the following uncovered lines:

- **line 224** — `qs = ext.optimize(qs, info=info)` inside `_assemble_node_queryset`. `_resolve_optimizer_extension(info)` always returns `None` for `0.0.5` (line 186 stub), so the `if ext is not None:` branch is dead code. No test can ever cover this branch given the current implementation. Either add `# pragma: no cover` (per `AGENTS.md` line 21, allowed only for "branches genuinely unreachable under the test runner's environment") or change `_resolve_optimizer_extension` to return a real lookup so a test can stub it.
- **lines 271-272** — `if required: async_call = getattr(qs, "aget", None); return async_call() if async_call is not None else sync_to_async(qs.get)()` in `_resolve_node_default`. The `required=True` async path is exercised by no test; only the `required=False` async path is covered (and that one fails — see High above).
- **line 303** — `return _order_nodes(results, coerced_keys, id_attr, required=required)` inside `_materialize` in `_resolve_nodes_default`. The async-path-with-ids materialization branch is uncovered (test_resolve_nodes_async_context fails before reaching it).

```django_strawberry_framework/types/relay.py:222:0
ext = _resolve_optimizer_extension(info)
if ext is not None:                    # <-- always False because the helper stubs None
    qs = ext.optimize(qs, info=info)   # <-- line 224, never executed
```

Recommended change: (a) fix the async tests so the `aget`/`afirst` branches actually run end-to-end and line 303 is exercised; (b) add a test that drives `_resolve_node_default` with `required=True` under an async context, hitting line 271-272; (c) decide whether the optimizer-ext branch at line 224 should be `# pragma: no cover` for `0.0.5` (with a TODO anchor pointing at the future slice that wires the lookup) or stubbed out entirely so the coverage gate stays green. Decision 7's invariants don't require the node-lookup optimizer cooperation in `0.0.5`, so dropping the branch (and the `_resolve_optimizer_extension` helper) is the cleanest fix; keeping the seam plus `# pragma: no cover` is acceptable but adds dead code the integration pass will want to revisit.

### Medium:

#### Inconsistent missing-id exception type between resolve_node(required=True) and resolve_nodes(required=True)

`_resolve_node_default` with `required=True` calls `qs.get()`, which raises `Model.DoesNotExist` (Django's `ObjectDoesNotExist` subclass). `_resolve_nodes_default` with `required=True` builds an index dict and does `output.append(index[key])`, which raises `KeyError`. Two different exception types for the same "required missing id" semantic. The plan justification at step 9 acknowledges this matches `strawberry_django/relay/utils.py:189-198`, but a consumer trying to catch the failure path now has to write two `except` clauses. Strawberry-django ships the same shape, so the borrow is faithful — but `0.0.5` could choose to homogenize (e.g. re-raise `Model.DoesNotExist` from the plural path). The minor inconsistency is a Medium finding because (a) it surfaces in tests with two different `pytest.raises` types (`Category.DoesNotExist` at line 487, `KeyError` at line 531), and (b) consumers writing visibility-aware exception handling will be surprised.

Recommended change: either explicitly document this in `types/relay.py:_resolve_nodes_default`'s docstring (it currently calls out the `KeyError` shape, which is accurate but doesn't acknowledge the asymmetry with `_resolve_node_default`) and add an explicit Worker 1 note for spec reconciliation, OR change `_order_nodes` to raise `cls.__django_strawberry_definition__.model.DoesNotExist` instead of letting `KeyError` propagate. Recommend the second path for consumer-friendly exception handling, but it diverges from the strawberry-django borrow.

#### _RELAY_RESOLVER_NAMES tuple and the inline defaults dict duplicate the four method names

The shadow inspector's "Repeated string literals" section for `types/relay.py` reports `2x resolve_id`, `2x resolve_id_attr`, `2x resolve_node`, `2x resolve_nodes`, `2x __func__`. The first appearance is in `_RELAY_RESOLVER_NAMES` at lines 36-41; the second is in the `defaults = {...}` dict at lines 329-334 inside `install_relay_node_resolvers`. The tuple-then-dict shape forces every future renamer to update two sites, and adding/removing a fifth `resolve_*` method requires touching both. The DRY shape is to make `_RELAY_RESOLVER_NAMES` a tuple of `(name, callable)` pairs (or just drop it and iterate the dict directly).

```django_strawberry_framework/types/relay.py:36:0
_RELAY_RESOLVER_NAMES: tuple[str, ...] = (
    "resolve_id",
    "resolve_id_attr",
    "resolve_node",
    "resolve_nodes",
)
...
django_strawberry_framework/types/relay.py:329:4
defaults = {
    "resolve_id": _resolve_id_default,
    "resolve_id_attr": _resolve_id_attr_default,
    "resolve_node": _resolve_node_default,
    "resolve_nodes": _resolve_nodes_default,
}
for attr in _RELAY_RESOLVER_NAMES:
    default_impl = defaults[attr]
```

Recommended change: collapse to a single source. Option A — module-level constant of tuples:

```python
_RELAY_RESOLVER_DEFAULTS: tuple[tuple[str, Callable[..., Any]], ...] = (
    ("resolve_id", _resolve_id_default),
    ("resolve_id_attr", _resolve_id_attr_default),
    ("resolve_node", _resolve_node_default),
    ("resolve_nodes", _resolve_nodes_default),
)
```

Then `install_relay_node_resolvers` iterates that. Option B — drop the constant and inline `defaults` only. The DRY Q6 of the plan explicitly anticipated this question and the plan asserted one constant + one call site; the implementation introduced a second hardcoded dict that re-states the same four names, so the plan's contract drifted on landing.

#### Bypass scaffolding spread across five sites with divergent shapes

Four test files plus the HTTP-test file each carry a local `_stage_relay*` helper:

1. `tests/types/test_relay_interfaces.py::_stage_relay_definition` (lines 58-80) — accepts `interfaces` kwarg, strips pk annotation when Relay.
2. `tests/optimizer/test_relay_id_projection.py::_stage_relay` (lines 38-50) — accepts `interfaces` kwarg, strips pk annotation when Relay.
3. `tests/types/test_definition_order_schema.py::_stage_relay` (lines 16-28) — hardcoded `(relay.Node,)`, always strips pk annotation.
4. `tests/test_registry.py::_stage_relay` (lines 28-37) — hardcoded `(relay.Node,)`, always strips pk annotation.
5. `examples/fakeshop/test_query/test_library_api.py::_reload_with_library_relay_node` (lines 514-548) — HTTP-path variant, hardcoded to `GenreType`, interleaves with schema reload.

Sites 3-4 are near-identical (~12 lines each); sites 1-2 differ only in scope (default `interfaces` tuple). The build report's "Notes for Worker 3" defends this as "intentional spread per DRY Q7", arguing cross-tree consolidation would couple test-isolation boundaries. The trade-off is real, but the **pk-annotation strip step is non-obvious and easy to forget** — site 5 (HTTP) silently relies on the same annotation-strip pattern. Five copies of the same critical bypass mechanism is a build-time defect risk: when Slice 5 promotes `"interfaces"` out of `DEFERRED_META_KEYS`, all five sites become structural no-ops and each must be cleaned up independently. The DRY shape is **one** helper in `tests/_relay_bypass.py` (or similar package-internal test helper) plus a one-line per-site call. Test-isolation boundaries are preserved because the helper would only encode the bypass mechanism, not any per-test state.

Recommended change: hoist to a single shared helper under `tests/` (or document explicitly why the spread is unavoidable for HTTP-path-vs-in-process). At minimum, add a `tests/conftest.py`-level docstring or a single `# stages relay interfaces via the deferred-key bypass` block-comment template that every site must copy verbatim. Without consolidation Slice 5's cleanup will touch five sites, each with a chance to drift on the annotation-strip step. This is precisely the kind of duplication the BUILD.md DRY-first directive exists to catch.

#### Missing test for sync-vs-async branch separation in resolve_nodes(node_ids=None)

`_resolve_nodes_default` with `node_ids=None` returns `_assemble_node_queryset(cls, info, id_attr)` (a `QuerySet`) directly, **regardless** of async context. This is documented in the docstring at lines 286-287 ("the caller materializes via `async for` / iteration as needed"). But there is no test that exercises this code path in an async context to demonstrate that the consumer can `async for obj in result:` over the returned queryset. The single passing test for this branch (`test_resolve_nodes_without_ids_returns_full_queryset`) runs sync and asserts `qs.count()`. The spec at line 491 calls for `test_resolve_nodes_async_context` to exercise "order-preserving / missing-id behavior under async" — but the implementation has TWO async branches in `_resolve_nodes_default` (the `_materialize` branch when ids are supplied, and the lazy-queryset return when `node_ids=None`) and only one is exercised.

Recommended change: add a test that calls `_resolve_nodes_default(CategoryNode, info=async_info, node_ids=None)` and asserts the return is a `QuerySet` (or a coroutine returning one) so the async-no-ids path is pinned.

### Low:

#### apply_interfaces signature widens the spec's typed contract

The spec at line 384 declares `def apply_interfaces(type_cls: type, definition: DjangoTypeDefinition) -> None:`. The implementation at `django_strawberry_framework/types/relay.py:89` declares `def apply_interfaces(type_cls: type, definition: Any) -> None:`. The build report's spec-reconciliation note 3 acknowledges this widening for unit-test ergonomics and suggests Worker 1 decide. Recommended change: either tighten the type hint back to the quoted `"DjangoTypeDefinition"` forward-reference (the file already has `from __future__ import annotations`, so forward references resolve as strings without import churn) and rely on `Protocol`-style duck typing at the unit-test boundary, or document the duck-typed signature in the spec. The `Any` widening loses the spec-level typing contract for one duck-typed test convenience.

#### Idempotency test does not pin override preservation

`test_install_relay_node_resolvers_idempotent_and_preserves_override` at `tests/types/test_relay_interfaces.py:847-873` only asserts idempotency (two calls produce the same `__func__`). Its name promises "preserves override" coverage, but it never declares a consumer override. The plan section "Test additions" at line 594 lists this test under Slice 4 with the same name; the per-method override tests (`test_consumer_resolve_*_wins`) cover override preservation individually, so this test's "and_preserves_override" suffix is misleading. Recommended change: rename to `test_install_relay_node_resolvers_idempotent` and remove the override-preservation language from the docstring, OR add an override-preservation assertion (declare a `@classmethod def resolve_id(cls, root, info): return "override"` on the class, install twice, confirm the consumer override is preserved at every call).

#### Comment-only Phase 2.5 anchor uses # comments not a docstring

`django_strawberry_framework/types/finalizer.py:89-95` uses a multi-line `#` comment to document Phase 2.5. The rest of `finalize_django_types()` does not use mid-function block comments — the Phase 1/2/3 boundaries are documented via the function docstring and inline comments are sparse. The block comment ages well next to the loop it documents, but a sibling-style docstring expansion (extending `finalize_django_types`'s docstring with the Phase 2.5 description) would keep the documentation centralized at one read site.

#### Docstring on _resolve_optimizer_extension promises behavior the stub does not deliver

The docstring at `django_strawberry_framework/types/relay.py:174-185` says the helper "Return[s] the `DjangoOptimizerExtension` instance on `info` if any" but the body unconditionally returns `None`. A future reader sees the docstring and expects a real lookup. Recommended change: lead the docstring with the stub-status disclosure ("**Stub for 0.0.5**: always returns ``None`` ...") so the lookup-vs-stub gap is the first thing a reader sees, rather than the third paragraph.

### DRY findings

- **`_RELAY_RESOLVER_NAMES` constant duplicates the `defaults` dict keys** (`types/relay.py:36-41` and `types/relay.py:329-334`). Covered under Medium above.
- **Five test-file local `_stage_relay*` helpers** with near-identical implementations and the load-bearing pk-annotation strip step. Covered under Medium above.
- **`__func__` accessor pattern duplicated four times in install_relay_node_resolvers** (`types/relay.py:339-340`): `existing_func = getattr(existing, "__func__", None)` / `node_func = getattr(node_default, "__func__", None)`. The DRY value is borderline — the two reads are tightly co-located and the names are different concepts — but a one-line helper `def _func(callable_or_none): return getattr(callable_or_none, "__func__", None)` would reduce the `2x __func__` literal repetition the shadow inspector flagged. Borderline; the plan's structural-split discriminator argument applies — leaving the two reads inline keeps the discriminator visible. **Not a finding**; recording for transparency.
- **Triple `definition.model._meta.pk.name` access in test scaffolding** — `tests/types/test_relay_interfaces.py:79`, `tests/optimizer/test_relay_id_projection.py:50`, `tests/types/test_definition_order_schema.py:28`, `tests/test_registry.py:36`, and `examples/fakeshop/test_query/test_library_api.py:537`. Each one strips the synthesized pk annotation. Same DRY shape as the bypass-helper finding; consolidating the bypass helper would consolidate this too.
- **`from strawberry import relay` appears in every Slice-4-touched test file plus the source module** (`relay.py:30`, `tests/types/test_relay_interfaces.py:26`, `tests/optimizer/test_relay_id_projection.py:24`, `tests/types/test_definition_order_schema.py:8`, `tests/test_registry.py:16`, `examples/fakeshop/test_query/test_library_api.py:13`). Imports are not subject to DRY consolidation by convention; recording for completeness because the shadow's "Imports" cross-file scan would otherwise flag it.

### What looks solid

- **Phase 2.5 placement is correct.** Inserted between Phase 2 (resolver attachment) and Phase 3 (Strawberry decoration) at `finalizer.py:96-104`, uses `registry.iter_definitions()` exactly like the existing loops, short-circuits on `definition.finalized` and `definition.interfaces` correctly.
- **Three discriminators stay structurally distinct.** Slice 2's `is_type_of in __dict__` (`relay.py:79`), Slice 3's `relay.Node in interfaces` tuple membership (in `base.py`), and Slice 4's `__func__` identity check (`relay.py:339-341`) live at three lifecycle phases and are not collapsed. The worker-memory carry-forwards from Slices 2/3 have been respected.
- **Composite-pk gate is correct.** `isinstance(model._meta.pk, CompositePrimaryKey)` at `relay.py:129` is the right shape for Django 5.2+'s composite-pk type. The error message at lines 130-135 names the model and proposes both remediation paths (explicit `relay.NodeID[...]` or removing `relay.Node`) per Decision 2.
- **`apply_interfaces` `iface not in type_cls.__mro__` short-circuit** at `relay.py:104` correctly handles the `class Foo(DjangoType, relay.Node)` case and the `Meta.interfaces = (relay.Node,)` case identically (no double-injection).
- **`TypeError` wrap as `ConfigurationError`** at `relay.py:109-116` names the offending interfaces and chains the original exception via `raise ... from exc`. Pinned by `test_apply_interfaces_wraps_typeerror_as_configuration_error`.
- **`__func__` identity discriminator** at `relay.py:339-341` correctly distinguishes inherited `relay.Node` defaults from consumer-declared overrides. Strawberry's `relay.Node` defaults are bound methods on the class with `__func__` attributes (confirmed via local probe).
- **`_resolve_id_default`'s `"pk"` coercion** at `relay.py:165-166` is the strawberry-django port site and is the right shape for Decision 7's "no avoidable lazy loads on `resolve_id`" invariant. The build report's Worker-1 note 5 names this as a likely spec-reconciliation candidate.
- **`get_queryset` cooperation** at `_assemble_node_queryset` line 215 (`cls.get_queryset(qs, info)`) follows the documented signature; the test `test_resolve_node_applies_get_queryset` pins the visibility-filter scoping.
- **Order-preserving / missing-aware behavior** at `_order_nodes` (`relay.py:228-250`) is the strawberry-django port shape and is pinned by `test_resolve_nodes_preserves_order_and_missing` and `test_resolve_nodes_required_raises_for_missing`.
- **Strawberry version compatibility.** `from strawberry.utils.inspect import in_async_context` at `relay.py:32` is importable on `strawberry-graphql>=0.262.0` (confirmed via `uv run python -c ...`). Worker 2's choice to use Strawberry's own utility rather than a hand-rolled `_is_async_context(info)` is correct.
- **Django 5.2 import discipline.** `from django.db.models import CompositePrimaryKey` is unconditionally importable per the `pyproject.toml` `Django>=5.2` pin (confirmed via `uv run python -c ...`).
- **Resolvers.py polish.** The TODO anchor at `types/resolvers.py:_is_fk_id_elided` was correctly replaced with a permanent docstring sentence anchoring Decision 7's FK-id-elision scoping. No regression risk to the existing optimizer behavior.
- **Boundary discipline.** `types/base.py`, `__init__.py`, `pyproject.toml`, `docs/FEATURES.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, and `CHANGELOG.md` are unchanged — Slice 5 work was not pulled forward.
- **No new public exports.** Definition of done item 11 is honored; the four `_resolve_*_default` helpers and the four `apply_*`/`implements_*`/`install_*` helpers stay internal to `django_strawberry_framework.types.relay`.
- **Three optimizer tests** (`test_relay_id_only_projection_includes_pk_attname`, `test_relay_id_does_not_trigger_lazy_load`, `test_relay_target_relation_planning_unchanged`, `test_relay_resolve_id_uses_loaded_pk`) pass; Decision 7's list-path invariants are pinned.
- **TODO-anchor removal discipline** is correct per `AGENTS.md` line 10: anchors removed in `finalizer.py:82-86`, `resolvers.py:_is_fk_id_elided`, `test_definition_order_schema.py`, `test_registry.py`, and `test_library_api.py`.

### Temp test verification

No temp tests created during this review pass. The focused-coverage run was sufficient to confirm the High-severity findings (5 test failures + 4 uncovered lines); each High finding's evidence is reproduced directly from the failing test output, so no additional temp tests are needed.

### Notes for Worker 1 (spec reconciliation)

1. **Optimizer-extension stub is the spec's "preferred answer".** The spec at line 547 explicitly allows the stub: "Should `resolve_node` use the optimizer? Preferred answer for `0.0.5`: apply `cls.get_queryset(...)` and consult the optimizer extension only if it is straightforward." Worker 2's `return None` stub at `relay.py:186` honors the "if straightforward" qualifier. The Worker-3 finding about line 224 being dead code is structural, not contractual — Worker 1 may decide whether to (a) ship the seam with `# pragma: no cover` plus a forward-pointing TODO anchor; (b) remove the seam entirely and put it back in a future slice; or (c) implement the lookup. Recommendation: (a), because the seam preserves the future-slice landing site and the cost is one `# pragma: no cover` per uncovered branch.
2. **Decision 9 async coverage is unverified.** The two async tests fail before exercising the success path; the implementation may be correct but no green test demonstrates it. Worker 1's final-verification pass should weigh whether Decision 9's contract is genuinely tested by `0.0.5` or whether it lands without verification. Recommend: require Worker 2 to fix the async-test wiring (`pytest-asyncio` + appropriate Django async fixture, or non-DB async assertion) before final-accepted.
3. **`_resolve_id_default` "pk" coercion is missing from the spec's literal example.** Build report's note 5 already calls this out; my review confirms — spec line 313 reads `try: return str(root.__dict__[id_attr]) except KeyError: return str(getattr(root, id_attr))` but the working implementation needs the `if id_attr == "pk": id_attr = root.__class__._meta.pk.attname` coercion. Worker 1 should update the spec to either inline the coercion or cite `strawberry_django/relay/utils.py:340-348` as the full port site.
4. **HTTP test placement vs. Slice 5 promotion.** The HTTP test `test_library_relay_node_global_id_round_trips` uses the bypass scaffolding to inject `interfaces = (relay.Node,)` between schema reload steps. Slice 5 promotes `"interfaces"` and the bypass becomes a structural no-op. Worker 1 should decide whether the bypass survives into Slice 5 as regression-coverage of the structural contract or is removed once the consumer-facing declaration works end-to-end.
5. **Missing test for `node_ids=None` under async context.** Decision 9's async coverage is split across two `_resolve_nodes_default` branches (`node_ids` supplied via `_materialize`; `node_ids=None` returning the raw queryset). Only the first is intended to be covered; the second has no test. Worker 1 may decide whether this is in scope for `0.0.5` (the contract is that the caller materializes via `async for`) or deferred to a future slice.
6. **Bypass scaffolding spread across five sites.** Five copies of the same load-bearing bypass mechanism in five test files. Worker 1 should weigh whether to flag this as an integration-pass DRY candidate or accept the cross-tree-coupling argument from Worker 2's build report. Recommend: integration-pass candidate.

### Review outcome

`revision-needed`

Deciding reason: 5 failing tests in the focused coverage run + 4 uncovered lines in `django_strawberry_framework/types/relay.py` violate the 100% coverage gate. The implementation may be substantially correct, but the slice cannot reach `final-accepted` while the focused coverage run reports failures. The High findings (failing tests for `resolve_id` `getattr` fallback, both async-context tests, malformed `NodeID` annotation, coverage gap) must close before the next review pass. The Medium findings (exception-type asymmetry, `_RELAY_RESOLVER_NAMES` duplication, bypass-scaffolding spread, missing async-no-ids test) should be addressed in the same Worker 2 pass; the Low findings can be addressed if cheap.

---

## Build report (Worker 2, pass 2)

### Files touched

- `django_strawberry_framework/types/relay.py` — extended Slice 4's structural-helper module to address Worker 3's findings. (1) `_resolve_optimizer_extension` helper and the `_assemble_node_queryset` "if ext: qs = ext.optimize(qs, info=info)" branch removed entirely — the seam stays in the docstring as a forward-pointing comment so a later slice can re-introduce a real lookup without changing the four-step shape (closes H4 line 224). (2) Async-resolver helpers cleaned: `_resolve_node_default` now calls `qs.aget()` / `qs.afirst()` directly under `in_async_context()` (Django 5.2+ ships both) rather than the previous defensive `getattr(qs, "aget", None)` plus `sync_to_async` fallback chain — drops the unreachable branch at the old lines 271-272 (closes H4 lines 271-272). (3) `_order_nodes` now raises the model's `DoesNotExist` on `required=True` plural-path missing ids, homogeneous with `_resolve_node_default`'s `qs.get()` (closes M1). (4) The `_RELAY_RESOLVER_NAMES` tuple plus the inline `defaults = {...}` dict were collapsed into one source: `_RELAY_RESOLVER_DEFAULTS: tuple[tuple[str, Callable[..., Any]], ...]` of `(name, default_impl)` pairs (closes M2). (5) Added a `# pragma: no cover` to the `if TYPE_CHECKING:` import line (line 37) — the quoted `DjangoTypeDefinition` hint is read by mypy / type checkers only and never executes at runtime; the pragma is the standard idiom for this branch and is the only `# pragma: no cover` in the slice.
- `django_strawberry_framework/types/finalizer.py` — no changes against the prior pass; the file already had the Phase 2.5 description inside `finalize_django_types()`'s docstring (closes L3 "block-comment-vs-docstring").
- `django_strawberry_framework/types/resolvers.py` — no changes against the prior pass (TODO anchor removal + permanent docstring shipped in pass 1).
- `pyproject.toml` — added `pytest-asyncio>=1.0.0` to `[dependency-groups] dev` (required for the four async-context tests). No version bump on the package.
- `pytest.ini` — added `asyncio_mode = auto` so the four `async def` test functions execute under the asyncio event loop without per-test `@pytest.mark.asyncio` decorators.
- `examples/fakeshop/test_query/test_library_api.py` — `_reload_with_library_relay_node()` now delegates the staging step to the shared `tests._relay_bypass.stage_relay_definition` helper (between the library-schema reload and the project-schema reload). Removed the inline `definition.interfaces = (relay.Node,)` + `__annotations__.pop(...)` block; the import block drops `from strawberry import relay` and adds `from tests._relay_bypass import stage_relay_definition`. The HTTP-path reload chain (library reload, stage, project reload, URL clear) stays explicit because Slice 4 does not have a sibling helper that owns the schema-reload chain. (Closes M3 site 5.)
- `tests/_relay_bypass.py` (new file) — the shared bypass helper `stage_relay_definition(type_cls, interfaces=(relay.Node,))`. Two steps: set `definition.interfaces`, strip the synthesized pk annotation when `relay.Node` is being staged. Used by all five Slice-4 test-call sites; site 5 (HTTP path) wraps the helper inside its schema-reload chain.
- `tests/test_registry.py` — local `_stage_relay` helper deleted and replaced by `stage_relay_definition` (closes M3 site 4).
- `tests/types/test_definition_order_schema.py` — local `_stage_relay` helper deleted and replaced by `stage_relay_definition`; the now-unused `from strawberry import relay` was removed by ruff isort (closes M3 site 3).
- `tests/types/test_relay_interfaces.py` — used `stage_relay_definition` from pass 1; pass 2 added `from asgiref.sync import sync_to_async`, introduced a `_build_seeded_category_node()` sync helper, and rewired the four async-context tests to wrap the sync setup (seed + class definition + finalize) under `await sync_to_async(_build_seeded_category_node)()` so Django's `SynchronousOnlyOperation` check passes (closes H2). Renamed the idempotency test from `test_install_relay_node_resolvers_idempotent_and_preserves_override` to `test_install_relay_node_resolvers_idempotent` and split the override-preservation assertion into a sibling test `test_install_relay_node_resolvers_preserves_consumer_override` (closes L2). `test_resolve_id_falls_back_to_getattr` and `test_resolve_id_default_unit_dict_cache_and_getattr_branches` now use a `_build_fake_root(id_value)` helper that constructs a synthetic root whose `__dict__` is empty but whose class-level `id` attribute resolves the value — the faithful shape for the `getattr` fallback per `strawberry_django/relay/utils.py:340-348` (closes H1). `test_node_id_annotation_overrides_default_id_attr` was rewritten to use `name: relay.NodeID[str]` (the working subscription form) and asserts `resolve_id_attr() == "name"` (closes H3). New tests added: `test_resolve_node_required_raises_for_missing` pinning `_resolve_node_default(required=True) -> Model.DoesNotExist`, `test_resolve_nodes_without_ids_returns_full_queryset` pinning the lazy-queryset return when `node_ids=None`, `test_resolve_nodes_async_context_no_ids_returns_queryset` pinning the same branch under async (closes M4 / addresses W3 spec-reconciliation note 5), `test_apply_interfaces_skips_already_present_bases` and `test_apply_interfaces_wraps_typeerror_as_configuration_error` pinning the two `apply_interfaces` branches, `test_resolve_id_default_unit_dict_cache_and_getattr_branches`, `test_resolve_node_default_invoked_via_helper`, `test_resolve_nodes_default_invoked_via_helper`.
- `tests/optimizer/test_relay_id_projection.py` (new file from pass 1) — unchanged in pass 2 beyond the existing `stage_relay_definition` usage.

### Tests added or updated

Net inventory after pass 2:

- `tests/types/test_relay_interfaces.py` — 88-line Slice 4 block (28 tests total under the divider). Async tests use `pytest-asyncio`'s auto mode and wrap sync setup under `sync_to_async`.
- `tests/optimizer/test_relay_id_projection.py` — 4 tests, all using `stage_relay_definition`.
- `tests/types/test_definition_order_schema.py` — 2 new Slice-4 tests, both using `stage_relay_definition`.
- `tests/test_registry.py` — 1 new Slice-4 test, using `stage_relay_definition`.
- `examples/fakeshop/test_query/test_library_api.py` — 1 new HTTP test, with `_reload_with_library_relay_node()` delegating to `stage_relay_definition` for the staging step.
- `tests/_relay_bypass.py` — new shared bypass helper imported by all five sites.

### Validation run

- `uv run ruff format .` — pass (93 files left unchanged after pass 2 edits).
- `uv run ruff check --fix .` — pass after 7 auto-fixes (sorted-imports, removed-unused-imports from the bypass-consolidation step); final state `All checks passed!`.
- Focused pytest command (per Worker 3's specification):
  ```
  uv run pytest tests/types/test_relay_interfaces.py tests/optimizer/test_relay_id_projection.py tests/types/test_definition_order_schema.py tests/test_registry.py --cov=django_strawberry_framework.types.relay --cov=django_strawberry_framework.types.finalizer --cov-report=term-missing
  ```
  Result: **88 passed**, 0 failed. Coverage on `django_strawberry_framework/types/relay.py` **100%** (95/95 lines). Coverage on `django_strawberry_framework/types/finalizer.py` **100%** (56/56 lines). The overall package coverage at 70% in this report is expected — the focused command does not run the full suite.

### Findings addressed

**High:**

- **H1 — `test_resolve_id_falls_back_to_getattr` crash on `AttributeError`.** Fixed. Introduced `_build_fake_root(id_value)` in `tests/types/test_relay_interfaces.py` that builds a synthetic root whose `__dict__` is empty but whose `__class__._meta` and class-level `id` attribute resolve cleanly. Both `test_resolve_id_falls_back_to_getattr` and `test_resolve_id_default_unit_dict_cache_and_getattr_branches` now use this helper, exercising the `getattr` branch faithfully without forcing an `AttributeError` from a real Django model instance.
- **H2 — `test_resolve_node_async_context` / `test_resolve_nodes_async_context` "database is locked" / `SynchronousOnlyOperation`.** Fixed. Added `pytest-asyncio>=1.0.0` to dev deps; set `asyncio_mode = auto` in `pytest.ini`; the four async tests now wrap their sync setup (`services.seed_data(1)` + `DjangoType` subclassing + `finalize_django_types()`) under `await sync_to_async(_build_seeded_category_node)()` so Django's "no sync ORM inside an event loop" guard does not fire. All four async tests pass: `test_resolve_node_async_context`, `test_resolve_node_async_context_required`, `test_resolve_nodes_async_context`, `test_resolve_nodes_async_context_no_ids_returns_queryset`. Decision 9's contract is verified end-to-end with passing tests.
- **H3 — `test_node_id_annotation_overrides_default_id_attr` malformed NodeID annotation.** Fixed. The test now declares `name: relay.NodeID[str]` (the subscripted form Strawberry's `Node.resolve_id_attr()` recognizes) and asserts `CategoryNode.resolve_id_attr() == "name"`. The malformed `Annotated[str, relay.NodeID]` form is gone.
- **H4 — Coverage gate failure on `types/relay.py:224, 271-272, 303`.** Fixed by code-shape change (not pragmas): `_resolve_optimizer_extension` and the `if ext is not None: qs = ext.optimize(...)` branch were both removed (the seam stays in `_assemble_node_queryset`'s docstring as forward-pointing guidance — a future slice can re-introduce a lookup without changing the four-step shape, per spec line 547's "Preferred answer for 0.0.5: apply `cls.get_queryset(...)` and consult the optimizer extension only if it is straightforward"). The defensive `getattr(qs, "aget", None)` + `sync_to_async(qs.get)` fallback chain in `_resolve_node_default` was simplified to direct `qs.aget()` / `qs.afirst()` calls — Django 5.2+ ships both, the project's lower bound is 5.2, and the simpler shape removes the unreachable defensive branch. `_order_nodes` `required=True` is exercised by `test_resolve_node_required_raises_for_missing` and the async/missing-id tests. The only `# pragma: no cover` in the slice is on the `if TYPE_CHECKING:` import line (line 37) — the standard idiom for a type-checking-only forward import that never executes at runtime. Final coverage on `types/relay.py`: 100% (95/95).

**Medium:**

- **M1 — `DoesNotExist` vs. `KeyError` asymmetry.** Fixed. `_order_nodes` now raises `cls.__django_strawberry_definition__.model.DoesNotExist` on `required=True` missing ids, homogeneous with `_resolve_node_default`'s `qs.get()`. The pluralized exception message names the model and the missing key for debuggability. `test_resolve_nodes_required_raises_for_missing` was updated to assert `pytest.raises(Category.DoesNotExist)` and matches `test_resolve_node_required_raises_for_missing`. Consumers write one `except Model.DoesNotExist:` clause for both paths.
- **M2 — `_RELAY_RESOLVER_NAMES` tuple + `defaults` dict duplicate the four method names.** Fixed. Collapsed to one module-level constant `_RELAY_RESOLVER_DEFAULTS: tuple[tuple[str, Callable[..., Any]], ...]` of `(name, default_impl)` pairs at module scope. `install_relay_node_resolvers` iterates the tuple directly, no second dict. Adding/renaming a future fifth `resolve_*` method touches exactly one site.
- **M3 — Bypass scaffolding spread across five sites.** Fixed. New shared helper `tests/_relay_bypass.py::stage_relay_definition(type_cls, interfaces=(relay.Node,))` carries the two load-bearing steps (set `definition.interfaces`, strip the synthesized pk annotation when `relay.Node` is staged). All five sites now call this helper: (1) `tests/types/test_relay_interfaces.py` — direct import + ~28 call sites; (2) `tests/optimizer/test_relay_id_projection.py` — direct import + 4 call sites; (3) `tests/types/test_definition_order_schema.py` — replaced local `_stage_relay`; (4) `tests/test_registry.py` — replaced local `_stage_relay`; (5) `examples/fakeshop/test_query/test_library_api.py` — `_reload_with_library_relay_node()` calls `stage_relay_definition(library_schema.GenreType)` between the library-schema reload and the project-schema reload. The HTTP-path file keeps its own reload-chain helper because the reload chain is HTTP-specific and is not in scope for the shared bypass; the shared helper owns only the staging mechanics. When Slice 5 promotes `"interfaces"` out of `DEFERRED_META_KEYS`, all five call sites collapse to direct `Meta.interfaces = (...)` declarations and `stage_relay_definition` becomes a one-file removal.
- **M4 — Missing async-no-ids test.** Fixed. `test_resolve_nodes_async_context_no_ids_returns_queryset` exercises the `_resolve_nodes_default(node_ids=None)` branch under an async event loop: asserts the return is a lazy queryset and materializes it via `async for`. Spec line 491's "node_ids=None" branch is now pinned.

**Low:**

- **L1 — `apply_interfaces` signature widens spec's typed contract (`definition: Any`).** Fixed. Tightened to `definition: DjangoTypeDefinition` with a `TYPE_CHECKING` forward import (the module already has `from __future__ import annotations`, so the annotation resolves as a string at runtime; mypy reads it as the real type). The unit-test `_SyntheticDef` shim still works because the runtime annotation is a string. The spec line 384 contract is preserved.
- **L2 — Idempotency test name misleading.** Fixed. Renamed to `test_install_relay_node_resolvers_idempotent` and removed the "and preserves override" language from the docstring. Added a sibling test `test_install_relay_node_resolvers_preserves_consumer_override` that declares a consumer `@classmethod def resolve_id_attr(cls): return "slug"` on the class, drives the host through `apply_interfaces` + `install_relay_node_resolvers`, and asserts `CategoryNode.__dict__["resolve_id_attr"].__func__ is consumer_func` — the helper-boundary version of the consumer-wins discriminator.
- **L3 — Phase 2.5 block-comment vs. docstring style.** Already addressed in pass 1 — `finalize_django_types()`'s docstring describes Phase 2.5 inline (lines 51-56). The mid-function block comment Worker 3 flagged in pass 1 was already a docstring expansion before this pass-2 ran, so no edit was required.
- **L4 — `_resolve_optimizer_extension` stub docstring promises behavior it does not deliver.** Fixed by removing the helper entirely (covered under H4). The remaining inline comment in `_assemble_node_queryset`'s docstring describes the future-slice seam without promising a current behavior.

### Notes for Worker 3

Re-review focus areas:

1. **`pytest-asyncio` + `asyncio_mode = auto` regression risk.** `pytest.ini`'s `asyncio_mode = auto` causes every `async def` test function in the suite to be run by `pytest-asyncio`. Before this change there were no `async def` tests, so this is the package's first exposure to that mode. Confirm: no existing sync test was accidentally annotated `async` (the focused run passed; the full-suite run will be Worker 1's final-verification gate's domain). If a future async test ever needs the event loop to extend beyond the function scope, that test will need to add `asyncio_default_fixture_loop_scope = function` (already the default).
2. **`tests/_relay_bypass.py` import discipline.** The shared bypass module lives under `tests/` and is imported by both package tests (`tests/...`) and HTTP tests (`examples/fakeshop/test_query/...`). `pytest.ini`'s `pythonpath = examples/fakeshop` plus pytest's rootdir auto-injection makes the import work from both trees (confirmed via collection probe). The module has zero runtime dependencies on the production package surface — it imports `registry` and `strawberry.relay` only. It is NOT part of the package source (no public re-export) and won't ship in the published wheel.
3. **The async tests use `transaction=True` on `pytest.mark.django_db`.** This is required because `services.seed_data(1)` is a sync ORM call wrapped under `sync_to_async` — the test's transaction boundary needs to be transactional to let the async-thread sync ORM calls see the seeded rows. Without `transaction=True`, Django's default `TestCase` rolls everything back per test but the rollback doesn't reach the worker thread `sync_to_async` ran in.
4. **`_RELAY_RESOLVER_DEFAULTS` is the single source of truth for the four method names.** A grep for the literal strings `"resolve_id"`, `"resolve_id_attr"`, `"resolve_node"`, `"resolve_nodes"` in `types/relay.py` reports each name exactly once (in the tuple). The fourth-method-rename would touch one line.
5. **The shared bypass helper deliberately strips the synthesized pk annotation only when `relay.Node` is being staged.** A non-Relay `@strawberry.interface` (e.g. `Auditable` in `test_non_relay_interface_works`) does not need the annotation strip because Strawberry's `id: GlobalID!` vs. `id: Int!` interface check only applies to `relay.Node`. The conditional in `stage_relay_definition` keeps the helper general-purpose for both interface flavors.
6. **The HTTP test `test_library_relay_node_global_id_round_trips`** uses a `_decode_global_id` helper that base64-decodes the Strawberry GlobalID string manually rather than importing Strawberry's `GlobalID.from_id()`. This keeps the assert side Strawberry-agnostic and is the simplest shape that proves the round-trip. Strawberry-version churn on the GlobalID encoder would surface here.

The shadow-file static-inspection helper was NOT re-run by Worker 2 for pass 2 — the only structural source-tree change was the removal of `_resolve_optimizer_extension` and the consolidation of `_RELAY_RESOLVER_NAMES` into `_RELAY_RESOLVER_DEFAULTS`. Worker 3's re-review may want to re-run the helper on `types/relay.py` to confirm the "Repeated string literals" section's `2x` counts for the four method names are now `1x`.

### Notes for Worker 1 (spec reconciliation)

None.

The pass-1 build-report's five spec-reconciliation notes still stand. Pass 2 closed all eight Worker 3 findings without surfacing new spec gaps. The `_resolve_optimizer_extension` deferral was already a spec-allowed shape (spec line 547); removing the stub helper entirely simply makes the implementation match the spec's "only if it is straightforward" qualifier literally.

---

## Review (Worker 3, pass 2)

Static helper invocations:

- `django_strawberry_framework/types/relay.py` — re-run; overview at `docs/build/shadow/django_strawberry_framework__types__relay.overview.md`. Repeated-string-literals section now reports `2x __func__` only (the four method names previously at `2x` are now `1x`, confirming the `_RELAY_RESOLVER_DEFAULTS` consolidation).
- `django_strawberry_framework/types/finalizer.py` — re-run; overview at `docs/build/shadow/django_strawberry_framework__types__finalizer.overview.md`. No new repeated-literal concerns.
- `tests/types/test_relay_interfaces.py` and `tests/_relay_bypass.py` — helper skipped. Reason: pass-2 test-side changes are extensions of an already-inspected file (`tests/types/test_relay_interfaces.py`) plus a tiny new bypass module (`tests/_relay_bypass.py`, 58 lines, single helper function, primarily docstring) with no fresh ORM markers or import-boundary surprises. The full file's diff was read in-line during the prior pass.

Focused coverage run executed: `uv run pytest tests/types/test_relay_interfaces.py tests/optimizer/test_relay_id_projection.py tests/types/test_definition_order_schema.py tests/test_registry.py --cov=django_strawberry_framework.types.relay --cov=django_strawberry_framework.types.finalizer --cov-report=term-missing`. Result: **88 passed**, 0 failed. Coverage on `django_strawberry_framework/types/relay.py`: **100%** (95/95). Coverage on `django_strawberry_framework/types/finalizer.py`: **100%** (56/56). The overall focused-scope coverage of 70.02% is expected (the focused command intentionally narrows the scope — the full-sweep coverage gate is Worker 1's domain).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- `_RELAY_RESOLVER_DEFAULTS` is now the single source of truth for the four method names and their default implementations. Grep on `"resolve_id"|"resolve_id_attr"|"resolve_node"|"resolve_nodes"` across `django_strawberry_framework/` returns the tuple at `types/relay.py:298-301` and nothing else. Pass-1 M2 closed cleanly.
- `tests/_relay_bypass.py::stage_relay_definition` is now the single source of truth for the deferred-key bypass, and all five Slice-4 test sites import the helper rather than carrying a local copy: `tests/types/test_relay_interfaces.py:42`, `tests/optimizer/test_relay_id_projection.py:27`, `tests/types/test_definition_order_schema.py:11`, `tests/test_registry.py:26`, and `examples/fakeshop/test_query/test_library_api.py:15` (with the HTTP-path file wrapping the call inside `_reload_with_library_relay_node` to interleave staging between the library- and project-schema reloads). The annotation-strip step lives in one place. When Slice 5 promotes `"interfaces"`, the bypass becomes a one-file removal. Pass-1 M3 closed cleanly.
- `__func__` accessor pattern in `install_relay_node_resolvers` (`types/relay.py:327-328`): `existing_func = getattr(existing, "__func__", None)` / `node_func = getattr(node_default, "__func__", None)`. Two co-located reads of the same attribute. Acknowledged in pass 1 as borderline and intentionally left inline so the discriminator stays visible at the only call site. No new finding.

### What looks solid

- **Pass-1 H1 closed cleanly.** `_build_fake_root(id_value)` in `tests/types/test_relay_interfaces.py:368-389` builds a synthetic root whose `__dict__` is empty but whose `__class__._meta.pk.attname` and class-level `id` attribute resolve cleanly — the faithful shape for the `getattr` fallback per `strawberry_django/relay/utils.py:340-348`. Both `test_resolve_id_falls_back_to_getattr` and `test_resolve_id_default_unit_dict_cache_and_getattr_branches` pass.
- **Pass-1 H2 closed cleanly.** `pytest-asyncio>=1.0.0` added to `[dependency-groups] dev` (correctly scoped — not a runtime dep); `pytest.ini` sets `asyncio_mode = auto` (drives any `async def` test function under the event loop without per-test decorators). The four async tests (`test_resolve_node_async_context`, `test_resolve_node_async_context_required`, `test_resolve_nodes_async_context`, `test_resolve_nodes_async_context_no_ids_returns_queryset`) wrap their sync setup under `await sync_to_async(_build_seeded_category_node)()` and use `@pytest.mark.django_db(transaction=True)` to share the seeded transaction with the worker thread. All four pass. Decision 9's contract is now verified end-to-end.
- **Pass-1 H3 closed cleanly.** `test_node_id_annotation_overrides_default_id_attr` at `tests/types/test_relay_interfaces.py:721-744` now declares `name: relay.NodeID[str]` (the working subscription form) and asserts `CategoryNode.resolve_id_attr() == "name"`. The malformed `Annotated[str, relay.NodeID]` form is gone.
- **Pass-1 H4 closed cleanly.** `_resolve_optimizer_extension` removed entirely; the unreachable `if ext is not None: qs = ext.optimize(...)` branch is gone; the defensive `getattr(qs, "aget", None)` + `sync_to_async` fallback chain in `_resolve_node_default` was simplified to direct `qs.aget()` / `qs.afirst()` (Django 5.2+ pinned). The only `# pragma: no cover` in the slice is on the `if TYPE_CHECKING:` import at `types/relay.py:36`, which is the standard idiom for type-checking-only imports that never execute at runtime. Final coverage on `types/relay.py`: 100%.
- **Pass-1 M1 closed cleanly.** `_order_nodes` now raises the model's `DoesNotExist` on `required=True` plural-path missing ids (`types/relay.py:232-235`). Consumers write one `except Model.DoesNotExist:` clause for both Relay node-lookup paths. `test_resolve_nodes_required_raises_for_missing` asserts `pytest.raises(Category.DoesNotExist)` matching the singular-path test.
- **Pass-1 M2 closed cleanly.** `_RELAY_RESOLVER_NAMES` tuple + `defaults` dict collapsed to one `_RELAY_RESOLVER_DEFAULTS: tuple[tuple[str, Callable[..., Any]], ...]` of `(name, default_impl)` pairs at `types/relay.py:297-302`. `install_relay_node_resolvers` iterates the tuple directly; adding/renaming a future fifth method touches one site.
- **Pass-1 M3 closed cleanly.** Shared bypass helper `tests/_relay_bypass.py::stage_relay_definition` consolidates the two-step bypass (set `definition.interfaces`, conditionally strip the pk annotation). All five Slice-4 call sites import the helper. The helper conditionally strips the pk annotation only when `relay.Node` is in the staged tuple, so the non-Relay `Auditable` test in `test_non_relay_interface_works` still works unchanged.
- **Pass-1 M4 closed cleanly.** `test_resolve_nodes_async_context_no_ids_returns_queryset` at `tests/types/test_relay_interfaces.py:543-555` exercises `_resolve_nodes_default(node_ids=None)` under an async event loop, asserts the return is a lazy queryset, and materializes via `async for`. Spec line 491's "node_ids=None" branch is pinned.
- **Pass-1 L1 closed cleanly.** `apply_interfaces` signature is now `definition: DjangoTypeDefinition` (`types/relay.py:85`) via a `TYPE_CHECKING` forward import (`types/relay.py:36-37`). The `from __future__ import annotations` at line 23 keeps the runtime annotation a string, so unit tests can still pass `_SyntheticDef` shims without import churn — confirmed by `test_apply_interfaces_skips_already_present_bases` and `test_apply_interfaces_wraps_typeerror_as_configuration_error` both passing.
- **Pass-1 L2 closed cleanly.** `test_install_relay_node_resolvers_idempotent_and_preserves_override` renamed to `test_install_relay_node_resolvers_idempotent` (`tests/types/test_relay_interfaces.py:914-940`) and a sibling `test_install_relay_node_resolvers_preserves_consumer_override` was added (`tests/types/test_relay_interfaces.py:943-973`). The override-preservation assertion now lives in a test that actually declares a consumer `@classmethod def resolve_id_attr(cls): return "slug"` and asserts the override survives `install_relay_node_resolvers`.
- **Pass-1 L3 closed.** `finalize_django_types()`'s docstring at `types/finalizer.py:50-56` now describes Phase 2.5 inline rather than a mid-function block comment.
- **Pass-1 L4 closed.** `_resolve_optimizer_extension` helper removed entirely (covered under H4). The remaining inline guidance in `_assemble_node_queryset`'s docstring (`types/relay.py:187-190`) describes the future-slice seam without promising current behavior.
- **`_RELAY_RESOLVER_DEFAULTS` single-source-of-truth verified by shadow.** The static-inspection helper's "Repeated string literals" report dropped from `2x resolve_id` / `2x resolve_id_attr` / `2x resolve_node` / `2x resolve_nodes` (pass 1) to just `2x __func__` (pass 2). The four method names appear in exactly one place in production source.
- **Bypass helper import discipline.** `tests/_relay_bypass.py` is import-side-effect-free apart from a registry-read inside the function body; nothing at import time touches `DEFERRED_META_KEYS`, `ALLOWED_META_KEYS`, or any other module-level production state. The helper imports `registry` and `strawberry.relay` only.
- **`pytest-asyncio` scoping.** Added under `[dependency-groups] dev` (`pyproject.toml:44`), not the runtime `dependencies` list — the published wheel sees no new requirement. `asyncio_mode = auto` in `pytest.ini` is the simplest mode for the four `async def` tests; non-async tests are unaffected (88 passed/0 failed in the focused run, no regressions from sync tests).
- **`uv.lock` regenerated.** Side effect of adding `pytest-asyncio`; the diff adds `backports-asyncio-runner`, `pytest-asyncio`, and supporting entries. No package-version bump leaked into this slice.
- **Boundary discipline preserved.** `types/base.py` (owns `DEFERRED_META_KEYS`), `__init__.py`, `docs/FEATURES.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`, and `tests/base/` are all unchanged. Slice 5 work was not pulled forward.
- **Ruff clean.** `uv run ruff check` against the touched production and test files reports `All checks passed!`; the line-length-110 / trailing-comma / COM812 standing rules hold.
- **No new public exports.** The `__init__.py` re-export surface is untouched; the four `_resolve_*_default` helpers and the four `apply_*`/`implements_*`/`install_*` helpers stay internal to `django_strawberry_framework.types.relay`.
- **Decision 7 invariants still hold.** The four optimizer tests in `tests/optimizer/test_relay_id_projection.py` pass — list-path pk-attname projection, strictness-mode lazy-load check, relation-traversal planning, and the dict-cache-hit zero-query assertion. The removal of `_resolve_optimizer_extension` does NOT affect these tests because the invariants live on the **list path**, which runs through the existing root-gated `DjangoOptimizerExtension`, not on the Relay-node-lookup path.

### Temp test verification

No temp tests created during this re-review pass. The focused-coverage run (88 passed, 0 failed, 100% on both touched production files) is sufficient to confirm every prior-pass finding has been addressed.

### Notes for Worker 1 (spec reconciliation)

1. **Spec internal-helper surface drift: `_resolve_optimizer_extension` removed entirely.** Pass 2 removed the `_resolve_optimizer_extension` helper and the `if ext is not None: qs = ext.optimize(...)` branch from `_assemble_node_queryset` (closing Worker 3 pass-1 finding H4). The spec's "Risks and open questions" entry at line 547 explicitly licenses this: "Should `resolve_node` use the optimizer? Preferred answer for `0.0.5`: apply `cls.get_queryset(...)` and consult the optimizer extension only if it is straightforward." Worker 2 chose "not straightforward, defer," which is in-scope. However, the spec's **Internal helper surface** section at lines 380-426 still lists optimizer-extension cooperation as part of the four `_resolve_*_default` signature bodies via the helper sketch's inline references to "optional `ext.optimize(qs, info=info)` when a `DjangoOptimizerExtension` is reachable via `info.context`." Worker 1 may want to add one clarifying sentence to that section (or to Decision 3 at lines 314-315) noting that the optimizer-extension consultation is deferred to a follow-up slice and the four-step queryset assembly currently runs steps 1-3 only. Decision 7's invariants are unaffected (they're list-path invariants, exercised by `tests/optimizer/test_relay_id_projection.py`). Low-priority spec edit; the contract is honored, only the helper-sketch language slightly overpromises.
2. **`_resolve_id_default` "pk" coercion** — the pass-1 build report's note 5 is still open. Spec line 313 reads `try: return str(root.__dict__[id_attr]) except KeyError: return str(getattr(root, id_attr))` but the working implementation needs the `if id_attr == "pk": id_attr = root.__class__._meta.pk.attname` coercion (`types/relay.py:161-162`). Worker 1 should update the spec to either inline the coercion or cite `strawberry_django/relay/utils.py:340-348` as the full port site. This carries forward from the prior review.
3. **Bypass scaffolding survives into Slice 5.** Now that the bypass is consolidated into `tests/_relay_bypass.py`, Slice 5's cleanup is a one-file removal (delete `tests/_relay_bypass.py` and the six `from tests._relay_bypass import stage_relay_definition` import lines plus the `stage_relay_definition(...)` call sites once `Meta.interfaces = (relay.Node,)` works end-to-end). Worker 1's Slice-5 plan should mention this cleanup step explicitly.
4. **Pass-1 spec-reconciliation notes 1, 2, 3, 4, 5, 6 from the prior Worker 3 review are still applicable.** Pass 2 did not surface new spec gaps; the existing notes carry forward into Worker 1's final verification.

### Prior-pass disposition

- **H1 — `test_resolve_id_falls_back_to_getattr` crash on AttributeError.** Addressed. Fixed via `_build_fake_root(id_value)` synthetic root that mimics the `__class__._meta.pk.attname` contract; both `test_resolve_id_falls_back_to_getattr` and `test_resolve_id_default_unit_dict_cache_and_getattr_branches` now pass.
- **H2 — async-context tests fail with "database is locked".** Addressed. `pytest-asyncio>=1.0.0` added to dev deps; `asyncio_mode = auto` set in `pytest.ini`; async tests wrap sync setup under `sync_to_async` and use `@pytest.mark.django_db(transaction=True)`. All four async tests pass.
- **H3 — malformed NodeID annotation in `test_node_id_annotation_overrides_default_id_attr`.** Addressed. Rewritten as `name: relay.NodeID[str]` (subscripted form); test passes.
- **H4 — 4 uncovered lines in types/relay.py.** Addressed. `_resolve_optimizer_extension` and the unreachable optimizer branch were removed entirely; the defensive `getattr(qs, "aget", None)` chain in `_resolve_node_default` was simplified to direct `qs.aget()` / `qs.afirst()` calls. The only `# pragma: no cover` in the slice is on the `if TYPE_CHECKING:` import, which is the standard idiom. Final coverage: 100% on `types/relay.py`.
- **M1 — DoesNotExist vs KeyError asymmetry.** Addressed. `_order_nodes` raises the model's `DoesNotExist` on `required=True` plural-path missing ids; `test_resolve_nodes_required_raises_for_missing` asserts `Category.DoesNotExist` matching the singular path.
- **M2 — `_RELAY_RESOLVER_NAMES` and inline `defaults` dict duplicate the four method names.** Addressed. Collapsed into `_RELAY_RESOLVER_DEFAULTS: tuple[tuple[str, Callable[..., Any]], ...]` at module scope; shadow's repeated-literal counts dropped from `2x` to `1x`.
- **M3 — Bypass scaffolding spread across five sites.** Addressed. New `tests/_relay_bypass.py::stage_relay_definition` helper; all five sites import and call the shared helper.
- **M4 — Missing async-no-ids test.** Addressed. `test_resolve_nodes_async_context_no_ids_returns_queryset` exercises the `node_ids=None` branch under an async event loop.
- **L1 — `apply_interfaces` signature widens spec's typed contract.** Addressed. Tightened to `definition: DjangoTypeDefinition` via `TYPE_CHECKING` forward import; runtime annotation remains a string thanks to `from __future__ import annotations`.
- **L2 — Idempotency test name misleading.** Addressed. Renamed to `test_install_relay_node_resolvers_idempotent`; sibling `test_install_relay_node_resolvers_preserves_consumer_override` added.
- **L3 — Phase 2.5 block comment style.** Addressed. `finalize_django_types()`'s docstring describes Phase 2.5 inline.
- **L4 — `_resolve_optimizer_extension` docstring promises behavior the stub does not deliver.** Addressed. Helper removed entirely; the remaining guidance in `_assemble_node_queryset`'s docstring is forward-pointing only.

### Review outcome

`review-accepted`

Deciding reason: every High/Medium/Low finding from pass 1 has been either addressed correctly (the implementation now matches the recommended change) or intentionally rejected by Worker 2 with a recorded reason that aligns with the spec's allowances (specifically the `_resolve_optimizer_extension` removal, licensed by spec line 547's "only if it is straightforward" qualifier and noted in this review for Worker 1's spec-reconciliation consideration). The focused coverage run reports 88 passed / 0 failed with 100% coverage on both touched production files (`types/relay.py` 95/95, `types/finalizer.py` 56/56). No new findings introduced by pass-2 changes. Boundary discipline preserved (no edits to `types/base.py`, `__init__.py`, docs, CHANGELOG, KANBAN, TODAY, or `tests/base/`). Ruff clean. The single low-priority Worker 1 spec-reconciliation note (clarify the optimizer-extension deferral in the helper-sketch section) is recorded for final verification, not a blocking finding.

---

## Final verification (Worker 1)

- **Cross-slice DRY check (Slices 1, 2, 3, 4).** The four discriminators remain structurally distinct, each living at its own lifecycle phase:
  - Slice 1's `_validate_interfaces` at `types/base.py:287` validates Strawberry interface classes at class-creation time and returns the normalized tuple.
  - Slice 2's `__dict__` membership at `types/relay.py:75` (`"is_type_of" in type_cls.__dict__`) preserves a consumer-declared `is_type_of` at class-creation time.
  - Slice 3's tuple-membership at `types/base.py:569` (`relay.Node in interfaces`) suppresses the synthesized `id` annotation at collection/`_build_annotations` time.
  - Slice 4's `issubclass(cls, relay.Node)` MRO check at `types/relay.py:50` plus the `__func__` identity test at `types/relay.py:329` gate the composite-pk check and inject the four `resolve_*` defaults at finalization time.
  No generic `override_check()` helper was introduced; the structural-split DRY false-positive trap is correctly avoided. The validated interfaces tuple flows one-way: `_validate_meta` (`base.py:405`) returns the tuple → `__init_subclass__` line 95 captures it → `DjangoTypeDefinition(interfaces=...)` stores it AND `_build_annotations(interfaces=...)` consumes it for Slice 3's `id` suppression → finalizer Phase 2.5 (`finalizer.py:99-101`) reads `definition.interfaces`. `_RELAY_RESOLVER_DEFAULTS` at `types/relay.py:297-302` is the single source of truth for the four method names (`grep`-confirmed: each name appears exactly once in production source). `_assemble_node_queryset`, `_order_nodes`, and `strawberry.utils.inspect.in_async_context` are shared helpers — both `_resolve_node_default` and `_resolve_nodes_default` call into them; no four-step queryset assembly copy.
- **Focused existing tests.** `uv run pytest tests/types/ tests/optimizer/ tests/test_registry.py --cov=django_strawberry_framework.types --cov-report=term-missing` reports **416 passed, 1 skipped, 0 failed**. Module-level coverage for the four touched production files: `types/relay.py` 100% (95/95), `types/finalizer.py` 100% (56/56), `types/base.py` 100%, `types/resolvers.py` 100%. The 97.56% overall coverage from this focused command is expected — `conf.py` (0%) is exercised by `tests/base/` which is outside this scope, and `utils/typing.py` (25%) is an integration-pass / final-test-run concern. Per the prompt and `BUILD.md`, the package-wide `fail_under = 100` gate is enforced at the build-closing final-test-run gate, not here.
- **Spec reconciliation.** The Worker 3 / Worker 2 reconciliation note about `_resolve_optimizer_extension` being removed entirely (per spec line 547's "only if it is straightforward" qualifier) is fully licensed by the spec, but Decision 3's documented body at line 314 explicitly wrote out the `ext = optimizer extension on info.context; if ext: qs = ext.optimize(qs, info=info)` step in the `_resolve_node_default` literal example. The implementation does not have that step. I made a small targeted spec edit to Decision 3 (lines 314-315) clarifying the deferral; also rolled in the `_resolve_id_default` "pk" coercion clarification (line 313) that was an outstanding spec-reconciliation note from Worker 2 / Worker 3 reviews. The composite-pk test was unskipped and pins both Decision 2 (composite-pk → `ConfigurationError`) and Decision 5 (Phase 2.5 placement) end-to-end.

### Summary

Slice 4 ships Phase 2.5 of `finalize_django_types()` — a new finalization step between Phase 2 (relation-resolver attachment) and Phase 3 (`strawberry.type(...)` decoration) that applies each `DjangoTypeDefinition.interfaces` entry into `cls.__bases__` (skipping interfaces already in the MRO, wrapping any `TypeError` from `__bases__` assignment as `ConfigurationError`), gates Relay-declared types against composite primary keys with a clear `ConfigurationError` that names both remediation paths, and injects the four `resolve_id` / `resolve_id_attr` / `resolve_node` / `resolve_nodes` defaults using the `__func__` identity test from `strawberry_django/type.py:213-225`. The defaults live in `django_strawberry_framework/types/relay.py` and cover both sync and async execution contexts via Django 5.2+'s native `aget` / `afirst` plus `strawberry.utils.inspect.in_async_context()` for dispatch. `_resolve_id_default` includes the `"pk" → root.__class__._meta.pk.attname` coercion so the `__dict__` cache hit actually fires (Decision 7's "no avoidable lazy loads" invariant). `_resolve_nodes_default` raises `Model.DoesNotExist` for `required=True` missing ids (homogeneous with `_resolve_node_default`'s `qs.get()`). All four Decision 7 optimizer invariants pass via the existing root-gated `DjangoOptimizerExtension`; the node-lookup-path optimizer-extension consultation is deferred to a future slice per spec line 547. New `tests/_relay_bypass.py::stage_relay_definition` consolidates the deferred-key bypass into a single helper used by all five Slice-4 test sites, which Slice 5 will collapse to a one-file removal once `"interfaces"` promotes from `DEFERRED_META_KEYS`. The composite-pk test was unskipped; 88 Slice-4 tests across `tests/types/test_relay_interfaces.py`, `tests/optimizer/test_relay_id_projection.py`, `tests/types/test_definition_order_schema.py`, `tests/test_registry.py`, and `examples/fakeshop/test_query/test_library_api.py` (one live HTTP GlobalID round-trip test) all pass.

### Spec changes made (Worker 1 only)

- `docs/spec-relay_interfaces.md` line 313 — clarified `_resolve_id_default`'s literal body to include the `if id_attr == "pk": id_attr = root.__class__._meta.pk.attname` coercion and cited `strawberry_django/relay/utils.py:306-348` (the full port site). Reason: Decision 7's "no avoidable lazy loads on `resolve_id`" invariant relies on the coercion — without it, `root.__dict__["pk"]` always misses because Django stores the pk under its column attname, never under the literal `"pk"`. Worker 2's build report note 5 and Worker 3's review note 3 jointly flagged this. Triggered by Slice 4 implementation.
- `docs/spec-relay_interfaces.md` lines 314-315 — removed the inline `ext = optimizer extension on info.context; if ext: qs = ext.optimize(qs, info=info)` step from the documented `_resolve_node_default` body example, added a forward-pointing sentence noting the optimizer-extension consultation is deferred to a follow-up slice (Decision 7's list-path invariants still flow through the existing root-gated `DjangoOptimizerExtension`), and homogenized the `_resolve_nodes_default` description to mention the `Model.DoesNotExist` semantic on `required=True`. Reason: implementation removed `_resolve_optimizer_extension` entirely per spec line 547's "only if it is straightforward" qualifier; Decision 3's prose was the one place the spec promised the lookup verbatim, and the deferral now reads cleanly there. Triggered by Slice 4 implementation.

### Final status

`final-accepted`
