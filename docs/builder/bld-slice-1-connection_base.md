# Build: Slice 1 — `DjangoConnection[T]` base + per-target concrete connection classes + `Meta.connection` validated and stored on the definition + the `first` + `last` guard

Spec reference: `docs/spec-030-connection_field-0_0_9.md` (Slice 1 checklist lines 75-80; Decision 3 lines 322-337; Decision 4 lines 339-359; Decision 8 lines 433-454; Test plan Slice 1 lines 559-567; Edge cases lines 541, 544-546, 553; DoD item 2 lines 646-648)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

**Existing patterns reused (cite file:line):**

- **Validator template — `_validate_filterset_class` / `_validate_orderset_class`** at `django_strawberry_framework/types/base.py:75-98` and `:101-126`. `_validate_connection` is structurally modeled on these: `None`-short-circuit when the key is unset, raise `ConfigurationError` (with `meta.model.__name__` in the message) on a bad value, return the normalized value otherwise. The spec (Decision 8, line 435) names this template explicitly. Note the difference from those two: `_validate_connection` ALSO needs the validated `interfaces` tuple to enforce the Relay-Node requirement, so unlike the filterset/orderset validators it takes a second input (the interfaces) — see Implementation step 4.
- **`_validate_meta` call site** at `django_strawberry_framework/types/base.py:624-730`. The two sidecar validators are invoked at `:696-697` and their results bundled into the `_ValidatedMeta` NamedTuple (`:603-621`, returned at `:720-730`). `connection` follows that exact threading: validate inside `_validate_meta`, add a field to `_ValidatedMeta`, return it in the snapshot. `interfaces` is already computed at `:695` (`interfaces = _validate_interfaces(meta)`) BEFORE the sidecar validators run, so `_validate_connection(meta, getattr(meta, "connection", None), interfaces)` can be called right after `:697` with the validated interfaces in hand — no re-derivation.
- **`_is_relay_shaped(cls, interfaces)`** at `django_strawberry_framework/types/base.py:198-209`. The Relay-Node predicate is already single-sited here. BUT it takes `cls` plus `interfaces`, and at `_validate_meta` time we only have `meta` (the validated `interfaces` tuple), not the owning `DjangoType` subclass. The Relay-Node check in `_validate_connection` is `any(issubclass(i, relay.Node) for i in interfaces)` — the `interfaces`-only half of `_is_relay_shaped`. Reuse the same `issubclass(i, relay.Node)` shape; do NOT try to thread `cls` into `_validate_meta` just to call `_is_relay_shaped` (the validator runs before the class object is fully usable, and `_validate_interfaces` already guarantees every entry is a Strawberry interface class). This is the one intentional partial-reuse; flag in Implementation discretion items.
- **`DjangoTypeDefinition` slot pattern** at `django_strawberry_framework/types/definition.py:88-95` (`primary` / `interfaces` / `filterset_class` / `orderset_class` slots, each a dataclass field with a default, documented in the class docstring at `:42-62`). The `connection` slot is added the same way: a typed field with a default placed alongside `filterset_class` / `orderset_class`, populated once in `__init_subclass__` from the validated value, read-only thereafter. The construction site is single (`DjangoTypeDefinition(...)` at `base.py:315-335`), so the new kwarg lands there exactly like `filterset_class=validated.filterset_class` (`base.py:333`).
- **`strawberry.relay.ListConnection`** (verified importable in the locked Strawberry `0.316.0`). `DjangoConnection[NodeType]` subclasses it. `ListConnection.resolve_connection` is a `@classmethod` with signature `(nodes, *, info, before, after, first, last, max_results, **kwargs)` (verified by inspection); the base carries only `page_info` / `edges` annotations — no `total_count`. The override delegates to `super().resolve_connection(...)`. Strawberry owns cursor math, `pageInfo`, edge wrapping, and the `first`/`last` slice window (`SliceMetadata.from_arguments`, verified to apply `first`+`last` without a mutual-exclusivity guard). We add only the guard and the count.
- **Test fixture conventions** at `tests/types/test_base.py`: the `"<key>" in ALLOWED_META_KEYS` / `not in DEFERRED_META_KEYS` membership-assertion shape (`:212-225`), the `pytest.raises(ConfigurationError, match=...)` validation-failure shape (`:266-274`), and the accept-and-store shape reading `definition = T.__django_strawberry_definition__; assert definition.<slot> is <value>` (`:277-293`). The `definition.connection` storage test mirrors `test_meta_filterset_class_accepts_filterset_subclass` (`:277-293`) one-for-one.

**New helpers / module justified (single responsibility each):**

- **`django_strawberry_framework/connection.py`** (net-new flat module, per Decision 14 / `docs/TREE.md` `connection.py [alpha]` slot). Slice 1's surface in it:
  - **`DjangoConnection[NodeType]`** — single responsibility: the generic `ListConnection[NodeType]` base that owns the package's `first` + `last` guard (Decision 3) and nothing else. No `total_count`.
  - **`_connection_type_for(target_type)`** — single responsibility: resolve (and cache, keyed on `target_type`) the connection class for a node type — bare `DjangoConnection[target_type]` when the type does not opt into `totalCount`, or a generated concrete `<TypeName>Connection` subclass when it does. Reads `definition.connection` (the new slot) to decide. This is the only place a connection class is constructed; Slice 2's factory and Slice 4's live usage both call it.
  - **The generated `<TypeName>Connection`** — single responsibility: carry `total_count: int` and override `resolve_connection` to selection-gate + count the post-filter pre-slice queryset and attach it to the connection instance. Generated by `_connection_type_for`, not hand-authored.
- **`_validate_connection(meta, connection, interfaces)`** in `types/base.py` — single responsibility: shape-check the `Meta.connection` dict (`{"total_count": bool}` only) and enforce the Relay-Node requirement, returning the normalized value or `None`. One call site: `_validate_meta`.
- **`connection` slot on `DjangoTypeDefinition`** — single responsibility: the canonical per-type record of the validated `Meta.connection` value, read by `_connection_type_for`.

**Duplication risk avoided:**

- **Re-parsing `Meta.connection` at connection-class-generation time.** The naive shape would have `_connection_type_for` reach back into `target_type.Meta` (or re-run a dict check). Decision 8 (line 442) forbids this: `Meta` is normalized away after validation. The plan stores the normalized value on `definition.connection` and has `_connection_type_for` read ONLY the definition — same discipline as `filterset_class` / `orderset_class`. Prevents a second, drifting copy of the opt-in logic.
- **A second Relay-Node predicate.** `_validate_connection`'s Relay check reuses the `issubclass(i, relay.Node)` shape already in `_is_relay_shaped` (`base.py:198-209`) rather than inventing a new spelling. (It cannot call `_is_relay_shaped` directly because that needs `cls`; see the partial-reuse note above and Implementation discretion items.)
- **Hand-rolling cursor / `pageInfo` / slice math.** Decision 3 (lines 330, 337) and the Borrowing posture (line 177) forbid it — Strawberry owns it. The override calls `super().resolve_connection(...)`; we never re-implement the window.
- **Duplicating the `total_count` field across opted-in types.** A per-target generated class keyed on `target_type` (Decision 4, line 346) means one connection shape per node type — no per-field variant, no naming/caching ambiguity. The cache prevents regenerating `<TypeName>Connection` on repeat calls.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — Slice 1 has not run yet, so these match HEAD, but re-check.

1. **Create `django_strawberry_framework/connection.py`** with `DjangoConnection`:
   - `class DjangoConnection(relay.ListConnection[NodeType], Generic[NodeType])` (or the Strawberry-idiomatic generic-subclass spelling that compiles against `0.316.0` — see Implementation discretion items). No `total_count` field.
   - Override `resolve_connection(cls, nodes, *, info, before=None, after=None, first=None, last=None, max_results=None, **kwargs)` (match the base classmethod signature, verified by inspection): when `first is not None and last is not None`, raise `GraphQLError("...")` (a query-runtime error landing in the response `errors` array — NOT `ConfigurationError`, per Decision 3 line 326 and Edge cases line 541). Otherwise `return super().resolve_connection(nodes, info=info, before=before, after=after, first=first, last=last, max_results=max_results, **kwargs)`.
   - Import `GraphQLError` from `graphql` (the package's established import for query-runtime errors — used in `filters`/`orders` `apply_*`; confirm the canonical import path during build).
   - Per the Build-plan public-export flag and Decision 14: Slice 1 does NOT add `DjangoConnection` to `django_strawberry_framework/__init__.py`. The symbol is referenced by its `connection.py` module path only until Slice 4.

2. **Add `_connection_type_for(target_type)` to `connection.py`:**
   - A module-level cache (e.g. `dict` keyed on `target_type`) — single source for connection classes; cleared concerns are noted below.
   - Read the node type's definition (`target_type.__django_strawberry_definition__`) and its new `definition.connection` slot.
   - When `definition.connection` is falsy / `None` or `total_count` is not requested → return the bare `DjangoConnection[target_type]` (generic specialization). Cache and return.
   - When `definition.connection == {"total_count": True}` → generate a concrete subclass named `f"{target_type.__name__}Connection"` (e.g. `GenreTypeConnection`) subclassing `DjangoConnection[target_type]`, declaring `total_count: int` (with the field-resolver reading a private instance attribute), and overriding `resolve_connection` to (a) keep the `first`+`last` guard — i.e. delegate to or re-share the base guard rather than duplicate it (see discretion item), (b) count ONLY when `totalCount` is in the selection set (read from `info`), (c) count the post-filter pre-slice `nodes` queryset via sync `.count()` (async `.acount()` is exercised by Slice 2's async path; Slice 1 may pin the sync count and the selection-gating logic), (d) attach the count to the connection instance, (e) delegate to `super().resolve_connection(...)` for slicing. Cache keyed on `target_type` and return.
   - Naming uniqueness is guaranteed by one-connection-shape-per-node-type (Decision 4 line 346); the cache prevents regeneration. (Registry-clear interaction: the cache is per-`target_type`-identity, and `target_type` classes are recreated fresh after `registry.clear()` in tests, so stale entries are bounded to discarded classes — same reasoning as the definition's `_related_target_cache` at `definition.py:96-106`. Note for Worker 2: if a `registry.clear()` hook needs to also clear this cache for test hygiene, that is a Worker 2 implementation detail — flag in Notes for Worker 1 if it surfaces.)

3. **`types/base.py` — grow `ALLOWED_META_KEYS`:** add `"connection"` to the `ALLOWED_META_KEYS` frozenset literal at `django_strawberry_framework/types/base.py:53-68` (alphabetical position: between `"interfaces"`/`"model"`-region — place to keep the set readable; the set is order-insensitive). Do NOT add it to `DEFERRED_META_KEYS` (`:49-51`). This mirrors `spec-029`'s net-new-key rule (the `nullable_overrides`/`required_overrides` precedent documented in the comment at `:69-72`); consider extending that comment to name `connection` as another net-new-ALLOWED key shipping in its own card.

4. **`types/base.py` — add `_validate_connection`:** new module-level helper modeled on `_validate_filterset_class` (`:75-98`). Signature `_validate_connection(meta: type, connection: Any, interfaces: tuple[type, ...]) -> dict | None`:
   - `if connection is None: return None`.
   - `if not isinstance(connection, dict)`: raise `ConfigurationError(f"{meta.model.__name__}.Meta.connection must be a dict; got {connection!r}")`.
   - Unknown sub-keys: `unknown = set(connection) - {"total_count"}`; if `unknown`: raise (`0.0.9` recognizes only `total_count`, per Decision 8 line 438 — typo guard).
   - `total_count` type: `if "total_count" in connection and not isinstance(connection["total_count"], bool)`: raise. (Decide bool-vs-`isinstance(x, bool)` excluding int subtleties during build; bool is the contract.)
   - Relay-Node requirement: `if not any(issubclass(i, relay.Node) for i in interfaces)`: raise `ConfigurationError(f"{meta.model.__name__}.Meta.connection requires Meta.interfaces to include strawberry.relay.Node ...")` (Decision 8 line 440; Edge cases line 553).
   - Return the normalized dict (the validated `connection` value).

5. **`types/base.py` — thread `connection` through `_validate_meta`:** in `_validate_meta` (`:624-730`), after the existing `interfaces = _validate_interfaces(meta)` at `:695` and the two sidecar validators at `:696-697`, add `connection = _validate_connection(meta, getattr(meta, "connection", None), interfaces)`. Add a `connection: dict | None` field to the `_ValidatedMeta` NamedTuple (`:603-621`) and include `connection=connection` in the returned snapshot (`:720-730`). (Field ordering in a NamedTuple is positional in the constructor call but the call uses keyword args, so placement is cosmetic — keep it next to `filterset_class`/`orderset_class` for readability.)

6. **`types/definition.py` — add the `connection` slot:** add `connection: dict | None = None` to `DjangoTypeDefinition` alongside `filterset_class` / `orderset_class` at `django_strawberry_framework/types/definition.py:93-94` (keep it before `finalized` at `:95`). Add a docstring bullet in the `Invariants:` block (`:23-71`) describing it, modeled on the `filterset_class` / `orderset_class` bullets at `:49-62`: populated by `DjangoType.__init_subclass__` from `Meta.connection`; consumed by `connection.py::_connection_type_for` to decide whether to emit the `totalCount` connection variant.

7. **`types/base.py` — store on the definition:** in `__init_subclass__`, add `connection=validated.connection,` to the `DjangoTypeDefinition(...)` construction at `:315-335` (next to `filterset_class=validated.filterset_class,` at `:333`). This is the single store site, mirroring the existing sidecar slots — no new branch added to the already-9-branch `__init_subclass__` hotspot (see static-inspection note below).

### Test additions / updates

Net-new file `tests/test_connection.py` (flat, mirroring `tests/test_list_field.py` per Decision 14 / `docs/TREE.md`). Pin these (spec Test plan lines 561-567). All can be earned package-internally — none of Slice 1's surface is reachable from a live `/graphql/` query yet (the field factory is Slice 2, live usage Slice 4), so `tests/test_connection.py` is the correct home per the `AGENTS.md` real-query-priority rule (the path is genuinely unreachable from a live query at this slice).

- `test_django_connection_is_listconnection_subclass` — `DjangoConnection[T]` (specialized over a Relay-Node-shaped `DjangoType`) is a `strawberry.relay.ListConnection` subclass and has no `total_count` field/annotation.
- `test_first_and_last_raises_graphql_error` — calling `DjangoConnection.resolve_connection(...)` (or the generated subclass's) with both `first` and `last` non-`None` raises `GraphQLError` (assert the exception type and a message substring; this is the package's own guard — `SliceMetadata.from_arguments` does not provide it, verified). Drive it directly at the classmethod with a minimal `nodes` / `info` double, since no field exists yet.
- `test_connection_type_for_caches_per_target` — `_connection_type_for(GenreType)` returns the SAME class object on repeat calls (cache identity); a `total_count`-enabled type yields a generated `<TypeName>Connection` that declares `total_count`; a non-opted Relay-Node type yields a bare `DjangoConnection[T]` (no `total_count`). Use one fixture type with `connection = {"total_count": True}` and one without.
- `test_total_count_present_only_when_opted_in` — the generated `<TypeName>Connection` exposes `total_count`; the bare `DjangoConnection[T]` for a non-opted type does not.
- `test_total_count_counted_only_when_selected` — `resolve_connection` on the opted-in class runs the count (sync `.count()`) ONLY when `totalCount` is in the selection set; with `totalCount` absent from the selection, no count is attempted / the attribute stays unset. Drive via a selection-set double on `info`; assert the post-filter pre-slice queryset is what's counted (count happens before the slice delegation).

`tests/types/test_base.py` additions (spec Test plan lines 565-567):

- `test_meta_connection_in_allowed_meta_keys` — `"connection" in ALLOWED_META_KEYS` and `"connection" not in DEFERRED_META_KEYS` (mirror `test_meta_filterset_class_is_promoted_to_allowed_meta_keys` at `test_base.py:212-217`).
- `test_meta_connection_non_dict_raises` — `Meta.connection = "nope"` (or any non-dict) on a Relay-Node-shaped type raises `ConfigurationError(match="must be a dict")`.
- `test_meta_connection_unknown_subkey_raises` — `Meta.connection = {"total_count": True, "bogus": 1}` raises `ConfigurationError` naming the unknown sub-key.
- `test_meta_connection_non_relay_type_raises` — `Meta.connection = {"total_count": True}` on a type whose `Meta.interfaces` omits `relay.Node` (or has no `interfaces`) raises `ConfigurationError(match="relay.Node")`.
- `test_meta_connection_stored_on_definition` — a Relay-Node-shaped type with `Meta.connection = {"total_count": True}` lands the normalized dict on `definition.connection` (mirror `test_meta_filterset_class_accepts_filterset_subclass` at `test_base.py:277-293`: `definition = T.__django_strawberry_definition__; assert definition.connection == {"total_count": True}`). Worker 2 should also confirm a type WITHOUT `Meta.connection` leaves `definition.connection is None` (the default), as a companion assertion or a sibling test.

Temp/scratch tests: none anticipated. The classmethod-level guard and count tests need lightweight `info` / `nodes` doubles (selection-set + a queryset stub exposing `.count()`); Worker 2 picks the double shape (real `GenreType` queryset vs. a minimal stub) — note for Worker 3 to confirm the double exercises the real branch (count called pre-slice, gated on selection).

### Implementation discretion items

These are choices Worker 1 has assessed and deliberately leaves to Worker 2 — each is a stylistic/mechanical equivalent, not an architectural question:

- **The generic-subclass spelling for `DjangoConnection`.** `class DjangoConnection(relay.ListConnection[NodeType])` with a `TypeVar`/`Generic[NodeType]` vs. whatever spelling compiles cleanly against the locked Strawberry `0.316.0` `ListConnection` generic. Both produce the same schema shape; Worker 2 picks the one that type-checks and instantiates. (If neither generic spelling works with `relay.connection` downstream, that is a Slice 2 concern flagged in the Build plan's argument-injection contingency — for Slice 1 only the class shape and the guard matter.)
- **How the generated `<TypeName>Connection` shares the `first`+`last` guard with the base.** Either inherits `resolve_connection` and calls `super()` for the guard before adding the count, or the guard is factored into a tiny shared helper both call. Worker 2 picks whichever reads cleaner without duplicating the `if first is not None and last is not None` check (DRY: do NOT copy the guard literal into two `resolve_connection` bodies).
- **The `total_count` field-resolver mechanism** (a `@strawberry.field`-decorated method reading a private attr vs. a plain annotation backed by an instance attribute set in `resolve_connection`). Decision 4 (line 344) says "a private attribute the `total_count` field resolver reads"; the exact Strawberry idiom is Worker 2's call as long as the count is per-instance (Decision 4 line 348 — not an `info.context` stash).
- **The module-level cache structure in `connection.py`** (`dict` vs. `functools.cache`-decorated function) and whether it participates in any `registry.clear()` reset. `dict` keyed on `target_type` is the obvious shape; `functools.cache` is acceptable. Flag to Worker 1 only if test hygiene forces a clear hook.
- **Alphabetical placement of `"connection"` in the `ALLOWED_META_KEYS` literal** and the exact `_validate_connection` error-message wording (must name `meta.model.__name__` and the offending value, matching the sibling validators' tone).
- **Whether `_validate_connection` lives immediately after `_validate_orderset_class`** (`base.py:126`) or elsewhere in the module — placement is cosmetic; keep it near the sibling validators.

Worker 1 has NOT delegated any architectural question here. The one non-obvious design call — that `_validate_connection` reuses the `issubclass(i, relay.Node)` half of `_is_relay_shaped` rather than calling `_is_relay_shaped(cls, interfaces)` — is resolved in the plan (Implementation step 4 / DRY analysis), not left to discretion: `_validate_meta` runs before the `cls` object is usable and `_is_relay_shaped` needs `cls`, so the interfaces-only check is the correct shape.

### Spec slice checklist (verbatim)

- [x] Ship [`django_strawberry_framework/connection.py`][connection] with a generic `DjangoConnection[NodeType]` subclass of [`strawberry.relay.ListConnection`][strawberry-relay] that has **no** `totalCount` field and overrides `resolve_connection` to raise a `GraphQLError` when both `first` and `last` are supplied, then delegates to `super().resolve_connection(...)` (the guard Strawberry's `SliceMetadata.from_arguments` does NOT provide).
- [x] A cached factory `_connection_type_for(target_type)` that returns the connection class for a node type: the bare `DjangoConnection[target_type]` when the type does not opt into `totalCount`, or a generated concrete subclass named `<TypeName>Connection` (e.g. `GenreTypeConnection`) declaring `total_count: int` and overriding `resolve_connection` to selection-gate + capture the count when it does. Cache keyed on `target_type` (one connection shape per node type — no per-field override, per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation), so no naming/caching ambiguity).
- [x] The `total_count` resolver reads a private instance attribute set by `resolve_connection`; `resolve_connection` counts the **post-filter pre-slice** `nodes` queryset (sync `.count()` / async `.acount()`) **only when `totalCount` is in the selection set** (per [Decision 4](#decision-4--djangoconnectiont-base-plus-per-target-concrete-connection-classes)), attaches it to the connection instance, then delegates to super for slicing.
- [x] [`django_strawberry_framework/types/base.py::ALLOWED_META_KEYS`][base] grows `"connection"` (net-new public key — NOT a [`DEFERRED_META_KEYS`][base] promotion, mirroring [`spec-029`][spec-029] [Decision 6][spec-029]). A `_validate_connection` helper (called from [`_validate_meta`][base], structurally modeled on `_validate_filterset_class`) shape-checks the dict (`{"total_count": bool}` only; unknown sub-keys and non-dict values raise) and rejects `Meta.connection` on a type whose `Meta.interfaces` omits `relay.Node`. The normalized value is **stored on [`DjangoTypeDefinition`][definition]** (a `connection` slot) so the factory and the connection-class generator can read it (per [Decision 8](#decision-8--metaconnection-opt-in-key-stored-on-the-definition)).
- [x] Package coverage: [`tests/test_connection.py`][test-connection] (the `DjangoConnection[T]` shape; the `first` + `last` `GraphQLError` guard; `<TypeName>Connection` generation + caching; `totalCount` present-only-when-opted-in and counted-only-when-selected). [`tests/types/test_base.py`][test-types-base] gains the `"connection"`-in-`ALLOWED_META_KEYS` / not-in-`DEFERRED_META_KEYS` assertion, the `_validate_connection` failure modes, and the `definition.connection` storage assertion.

### Static inspection findings (Worker 1, planning)

Ran per BUILD.md "When to run the helper during build" (Slice 1 adds logic to files under `types/`). `connection.py` is net-new — nothing to inspect there yet (Worker 3 inspects it at review).

- `docs/shadow/django_strawberry_framework__types__base.overview.md`: `__init_subclass__` is already a control-flow hotspot (125 lines, 9 branches, shadow line 217 → source `:217`) and `_validate_meta` is a hotspot (107 lines, 11 branches, source `:624`). **Implication for the plan:** add NO new branch to either. The `connection` store in `__init_subclass__` is a single kwarg on the existing `DjangoTypeDefinition(...)` call (step 7) — zero new branches. `_validate_connection`'s branching lives in the new helper (a fresh small function modeled on the sibling validators), not inlined into `_validate_meta` (step 4-5) — `_validate_meta` gains one straight-line call, no branch. This keeps both hotspots from worsening. Repeated string literals already include `filterset_class`/`orderset_class` (2x each, shadow lines 279-282); the new `connection` key is a single literal in `ALLOWED_META_KEYS` plus the validator — no new repeated-literal risk (the `"total_count"` string appears in the validator and the generator; if it repeats 2x watch for a named constant at integration, but two sites is below the threshold).
- `docs/shadow/django_strawberry_framework__types__definition.overview.md`: `DjangoTypeDefinition` is a small dataclass (172 lines, single hotspot `related_target_for` at source `:121`, unrelated to this slice). The `connection` slot is a pure dataclass-field addition with a default (step 6) — no logic, no new hotspot, no marker churn. Safe.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/connection.py` — NET-NEW. `DjangoConnection[NodeType]` (generic `relay.ListConnection` subclass, no `total_count`, `resolve_connection` override applying the `first`+`last` guard then delegating to super); `_guard_first_and_last` (single-sited guard helper, reused by base + generated subclass — no duplicated literal); `_total_count_requested` (recursive `info.selected_fields` walk for the camelCase `totalCount` field, modeled on strawberry-django's `_should_optimize_total_count`); `_connection_type_for(target_type)` (cache keyed on `target_type`, reads `definition.connection`); `_build_total_count_connection` (generates `<TypeName>Connection` via `types.new_class`, declaring `total_count` field + count-on-resolve override); `_attach_count_sync` / `_attach_count_async` (attach the pre-slice count to the resolved connection instance, handling super's sync-instance vs async-coroutine return).
- `django_strawberry_framework/types/base.py` — added `"connection"` to `ALLOWED_META_KEYS` (alphabetical first); extended the net-new-ALLOWED-key comment to name spec-030 Decision 8; added `_validate_connection(meta, connection, interfaces)` after `_validate_orderset_class` (dict-shape + unknown-subkey + bool + Relay-Node checks, returns normalized value); added `connection: dict | None` to the `_ValidatedMeta` NamedTuple; threaded `connection = _validate_connection(...)` into `_validate_meta` after the sidecar validators (reusing the already-validated `interfaces` tuple); added `connection=connection` to the `_ValidatedMeta` return; added `connection=validated.connection` to the single `DjangoTypeDefinition(...)` construction in `__init_subclass__` (zero new branches — one kwarg on the existing call).
- `django_strawberry_framework/types/definition.py` — added the `connection: dict | None = None` dataclass field (before `finalized`) and an `Invariants:` docstring bullet describing it, modeled on the `filterset_class` / `orderset_class` bullets.
- `tests/test_connection.py` — NET-NEW. See "Tests added or updated".
- `tests/types/test_base.py` — added the `Meta.connection` validation + storage tests (see below), inserted after `test_meta_filterset_class_accepts_filterset_subclass`.

### Tests added or updated

`tests/test_connection.py` (new, 14 tests):

- `::test_django_connection_is_listconnection_subclass` — `DjangoConnection` is a `relay.ListConnection` subclass with no `total_count`; the parametrized form's `__origin__` is `DjangoConnection`.
- `::test_first_and_last_raises_graphql_error` — `DjangoConnection.resolve_connection(..., first=1, last=1)` raises `GraphQLError("...mutually exclusive...")` (the package's own guard).
- `::test_first_and_last_guard_on_generated_subclass` — the generated `<TypeName>Connection` shares the guard.
- `::test_connection_type_for_caches_per_target` — identity caching per `target_type`.
- `::test_connection_type_for_generates_named_subclass_when_opted_in` — opted-in type yields `<TypeName>Connection` declaring `total_count`, subclass of `DjangoConnection`.
- `::test_connection_type_for_returns_bare_connection_without_opt_in` / `::..._when_total_count_false` — non-opt and `{"total_count": False}` both yield the bare generic alias (origin `DjangoConnection`, no `total_count`).
- `::test_total_count_present_only_when_opted_in` — `totalCount` in the SDL for an opted-in type, absent for a bare one (real `strawberry.Schema` build).
- `::test_total_count_requested_true_when_selected` / `::..._false_when_absent` — `_total_count_requested` selection-walk unit tests.
- `::test_total_count_counts_post_filter_pre_slice_when_selected` — real `execute_sync` query: `first: 1` slices `edges` to one but `totalCount` reflects the full pre-slice count.
- `::test_total_count_not_counted_when_not_selected` — a query omitting `totalCount` resolves correctly (no count); the same schema returns the count when `totalCount` IS selected (per-query gating, not type-wide).
- `::test_first_and_last_graphql_error_through_schema` — the guard surfaces in the GraphQL `errors` array via a real query.
- `::test_total_count_async_path_counts_via_acount` — real async `execute`; the async branch counts via `.acount()` and attaches it.

`tests/types/test_base.py` (extended, 7 tests):

- `::test_meta_connection_in_allowed_meta_keys` — `"connection"` in `ALLOWED_META_KEYS`, not in `DEFERRED_META_KEYS`.
- `::test_meta_connection_non_dict_raises` / `::..._unknown_subkey_raises` / `::..._non_bool_total_count_raises` / `::..._non_relay_type_raises` — the four `_validate_connection` failure modes raise `ConfigurationError`.
- `::test_meta_connection_stored_on_definition` — the normalized dict lands on `definition.connection`.
- `::test_meta_connection_absent_leaves_definition_none` — a type without `Meta.connection` leaves `definition.connection is None` (the plan's companion assertion).

### Validation run

- `uv run ruff format .` — pass (idempotent; no files changed on the final run).
- `uv run ruff check --fix .` — pass (`All checks passed!`).
- `uv run python scripts/check_trailing_commas.py <touched files>` — pass (collapsed the `_validate_connection` signature to one line, below the 4-item threshold; owned this drift here, re-runs are now `Fixed 0 file(s)`).
- `git status --short` after both ruff invocations:
  - Slice-intended (stay): `django_strawberry_framework/connection.py` (new), `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `tests/test_connection.py` (new), `tests/types/test_base.py`, plus the artifact + build plan.
  - Baseline-dirty (left untouched): `docs/GLOSSARY.md` (carried per the build plan; NOT reverted, NOT edited).
  - Pre-flight cleanup (not my changes): the seven `D docs/builder/*029*` / `bld-*` deletions are Worker 0's prior-cycle artifact removal, left as-is.
  - No unrelated tool churn from the ruff/comma runs.
- Focused tests (no `--cov*`): `uv run pytest tests/test_connection.py tests/types/test_base.py --no-cov` → 92 passed. Regression sweep `uv run pytest tests/types/ tests/test_registry.py tests/test_list_field.py --no-cov` → 360 passed, 2 skipped.

### Implementation notes

- **Generated-class construction uses `types.new_class`, not `type(...)`.** Plan-vs-implementation: the plan sketched `type(f"{name}Connection", (DjangoConnection[target_type],), {...})`. That fails with `TypeError: type() doesn't support MRO entry resolution` because `DjangoConnection[target_type]` is a subscripted generic alias. `types.new_class(name, (DjangoConnection[target_type],), exec_body=...)` is the correct primitive for subclassing a parametrized generic. Mechanically obvious within the slice contract; recorded here per the small-drift rule.
- **The bare path returns the generic alias `DjangoConnection[target_type]`, not a class.** Verified `relay.connection(DjangoConnection[T], resolver=...)` builds a valid schema and Strawberry auto-names it `<TypeName>Connection` with no `totalCount`. The bare-path tests assert on `__origin__` rather than `issubclass` (a generic alias is not a class). This matches the spec User-facing-API shape (`DjangoConnection[GenreType]` is a type annotation).
- **Guard is single-sited in `_guard_first_and_last`.** Both the base and the generated subclass call it — the `if first is not None and last is not None` literal lives once (the plan's discretion item explicitly forbade copying it into two bodies).
- **Count attachment splits sync vs async.** `super().resolve_connection(...)` returns a connection instance on the sync branch and a coroutine on the async branch (verified by reading `ListConnection.resolve_connection`). `_attach_count_sync` sets the attr directly; `_attach_count_async` awaits the coroutine first. Mirrors strawberry-django's `DjangoListConnection.resolve_connection` `inspect.isawaitable` split, but the package counts inside `resolve_connection` (selection-gated) and stores the int, per spec Decision 4(c)/(d), rather than deferring the count to the field resolver as strawberry-django does.
- **Count tests driven through a real in-process schema, not an `info` double.** A `SimpleNamespace` `info` double is insufficient for the real slicing path (`SliceMetadata.from_arguments` reads `info.schema.config.relay_max_results`). `_total_count_requested` is unit-tested with a thin double (it only reads `.name` / `.selections`), but the count + gating behavior is earned through `schema.execute_sync` / `schema.execute` — the most honest exercise of the real `info` and slicing, consistent with AGENTS.md's test-through-real-usage rule.
- **Cache hygiene in tests.** The autouse fixture clears `_connection_type_cache` alongside the registry; function-scope `DjangoType` fixtures are recreated each test, so a discarded class could otherwise leak into a later identity check. No `registry.clear()` hook into the module cache was needed in production code (test-local clearing suffices), so none was added — flagged below for Worker 1.

### Notes for Worker 3

- No shadow file was used for `connection.py` (net-new; Worker 3 inspects it at review per BUILD.md). The static-inspection note in the plan applies to `types/base.py` / `definition.py` — confirmed no new branch added to the `__init_subclass__` (one kwarg) or `_validate_meta` (one straight-line call) hotspots.
- `_total_count_requested` selection-walk: the recursion descends `selection.selections`; the camelCase `"totalCount"` literal is the GraphQL field name (not the Python `total_count`). Verified against `info.selected_fields` structure in the locked Strawberry `0.316.0`.
- The async count test runs under `pytest-asyncio` AUTO mode (the suite's mode); `in_async_context()` is True inside the coroutine, so `ListConnection`'s async branch returns a coroutine and `_attach_count_async` is exercised (the count came back correct via `.acount()`).
- `_build_total_count_connection`'s nested `resolve_connection` closes over `generated` (the class object assigned right after `types.new_class`); the closure resolves at query time when `generated` is bound — confirmed by the passing count tests.

### Notes for Worker 1 (spec reconciliation)

- **`types.new_class` vs `type(...)` (small drift, recorded above).** The plan's `type(...)` sketch cannot subclass a parametrized generic; `types.new_class` is the required primitive. Within the slice contract; no spec edit needed unless you want the spec/plan to name the primitive.
- **No production cache-clear hook.** The plan (step 2) raised the possibility that `registry.clear()` might need to also clear the connection-type cache for test hygiene. It did not — clearing the module cache in the test fixture suffices, and production code never calls `registry.clear()` outside tests. No `registry.clear()` hook was added. If a future slice (e.g. Slice 4 live usage interacting with finalization re-runs) needs production-side cache invalidation, that is a follow-up; flagging so it is not assumed delivered here.
- **Count lives inside `resolve_connection` (spec-faithful), differing from strawberry-django.** strawberry-django defers the count to a lazy field resolver; the spec (Decision 4) wants the count captured in `resolve_connection` (selection-gated) and attached to the instance, which is what landed. No conflict — just noting the deliberate divergence from the borrowed reference for the integration DRY pass.

---

## Review (Worker 3)

Reviewed Worker 2's diff against spec-030 Slice 1 (checklist lines 75-80; Decisions 3/4/8; Test plan lines 559-567; Edge cases lines 541, 544-553). Static helper run per BUILD.md ("Slice 1 adds a new `.py` file + touches `types/`"): `connection.py`, `types/base.py`, `types/definition.py` all inspected via `scripts/review_inspect.py --output-dir docs/shadow`. Focused tests re-run green (92 passed, no `--cov*`). Three behaviors verified empirically against the locked Strawberry `0.316.0` via in-process schema builds (see findings).

### High:

None.

### Medium:

#### M1 — `totalCount`-selected over a non-QuerySet source yields a confusing non-null violation (cross-slice seam to Slice 2)

The generated `<TypeName>Connection.totalCount` renders `Int!` (non-null) — verified by rendering the SDL: `totalCount: Int!`. The count is attached only when `want_count and isinstance(nodes, models.QuerySet)` (`connection.py::_attach_count_sync` / `_attach_count_async` #"isinstance(nodes, models.QuerySet)"). When `nodes` is a non-QuerySet iterable (e.g. a plain `list`) AND `totalCount` is selected, no count is attached, the field resolver returns `None`, and GraphQL raises `Cannot return null for non-nullable field <Type>Connection.totalCount` — confirmed reachable:

```text
ERRORS: [GraphQLError('Cannot return null for non-nullable field ListNodeConnection.totalCount.', ... path=['items', 'totalCount'])]
```

Why it matters: Decision 7's consumer-`resolver=` contract (spec lines 277-283, Edge cases line 548) says a non-queryset iterable with `filter:`/`orderBy:` input raises a clear `GraphQLError`, but says nothing about the `totalCount`-selected-over-a-non-queryset case. The result is a generic non-null engine error instead of a clear package message, OR an argument that `totalCount` should be unavailable / nullable when the source cannot be counted.

Scope note: this is NOT reachable through Slice 1's own surface — Slice 1 has no field factory; every Slice 1 path feeds a QuerySet. It becomes reachable only once Slice 2 ships the consumer-`resolver=` contract that admits non-queryset iterables. The count helpers that produce the gap (`_attach_count_*`) land in Slice 1, so it is recorded here and **escalated to Worker 1** (resolution needs the Decision 7 spec contract Worker 2 cannot edit). Recommended resolution paths under Notes for Worker 1.

Test expectation when fixed: a Slice 2 test that a `totalCount`-selected query over a consumer resolver returning a non-queryset iterable produces a clear package `GraphQLError` (not the engine's non-null violation), or asserts the agreed alternative shape.

### Low:

#### L1 — `first` + `last` guard executes twice on the opted-in path

The generated `<TypeName>Connection.resolve_connection` calls `_guard_first_and_last(first, last)` (`connection.py::_build_total_count_connection #"_guard_first_and_last(first, last)"`), then delegates via `super(generated, cls).resolve_connection(...)`, whose next MRO hop is `DjangoConnection.resolve_connection` — which runs `_guard_first_and_last` AGAIN before reaching `ListConnection`. Verified MRO: `MroNodeConnection → DjangoConnection → ListConnection → ...`. The guard is idempotent (same args, pure check) so this is harmless, but the explicit call in the generated body is redundant given the super chain already enforces it. Either drop the explicit call in the generated override (rely on the inherited `DjangoConnection` guard) or add a one-line comment that the double-run is intentional defensiveness. Not a correctness bug; no test change required. The literal itself is correctly single-sited in `_guard_first_and_last` (the plan's discretion item was honored).

#### L2 — `total_count` field carries two annotation sources with mismatched nullability

`_build_total_count_connection` sets `namespace["__annotations__"] = {"total_count": int}` AND assigns a `@strawberry.field`-decorated `total_count(self) -> int | None` resolver to the same attribute. The `__annotations__` (`int`) wins for the GraphQL type → SDL renders `Int!` (verified), so behavior is correct, but the resolver's `-> int | None` is inconsistent with the non-null field it backs. Since the field is selection-gated (the resolver only executes when `totalCount` is selected, by which point `resolve_connection` has set the attribute over a QuerySet source), `int` is the honest return type. Consider `-> int` for clarity, and note that the dual annotation source is slightly surprising. (Interacts with M1: the `int | None` resolver is exactly what lets the non-QuerySet path return `None` into an `Int!` field.) Low / clarity.

### DRY findings

- **`_validate_connection` genuinely reuses the validator template — confirmed.** `types/base.py::_validate_connection` follows `_validate_filterset_class` / `_validate_orderset_class` one-for-one: `None`-short-circuit, `ConfigurationError(f"{meta.model.__name__}.Meta.connection ...")` messages in the sibling tone, return the normalized value. It is NOT a copy — the body is genuinely different (dict-shape + unknown-subkey + bool + Relay-Node checks vs. the siblings' single `issubclass` check). The Relay-Node check reuses the `issubclass(i, relay.Node)` shape from `_is_relay_shaped` (`types/base.py::_is_relay_shaped`) rather than inventing a new spelling; calling `_is_relay_shaped(cls, interfaces)` directly is correctly avoided because `cls` is not usable at `_validate_meta` time (the plan's one intentional partial-reuse, justified).
- **`DjangoTypeDefinition` slot pattern reused exactly.** The `connection: dict | None = None` slot sits alongside `filterset_class` / `orderset_class`, is populated once in `__init_subclass__` via a single `connection=validated.connection` kwarg on the existing `DjangoTypeDefinition(...)` call (zero new branches added to the `__init_subclass__` hotspot, as planned), threaded through `_ValidatedMeta` and `_validate_meta` identically to the sidecar slots. No drift.
- **`first` + `last` guard literal single-sited.** `_guard_first_and_last` holds the `if first is not None and last is not None` check once; both the base and the generated subclass reference it. No copied literal. (The double-execution at runtime is L1, a control-flow note, not a literal-duplication DRY defect.)
- **Strawberry owns cursor/pageInfo/slice math.** Both `resolve_connection` overrides delegate to `super().resolve_connection(...)`; no hand-rolled window. Matches Decision 3 / Borrowing posture.
- **Repeated literal `"total_count"` (3x in `connection.py`, per the shadow overview).** Appears in the `_validate_connection`/generator opt-in read (`connection_options.get("total_count")`), the annotation dict, and the field-name. This is the GraphQL/Meta sub-key contract string; 3 sites is at the threshold but the three uses are semantically distinct (Meta sub-key read, Python field annotation, resolver name). Not worth a constant for Slice 1; flagged for the integration pass to watch if Slice 2 adds more `"total_count"` sites. No action this slice.
- **Test local-import pattern (`from strawberry import relay` per-test) in `tests/types/test_base.py`** matches the file's pre-existing convention (lines 310/324/338/363/378 predate this slice). Not a DRY violation against the file's own style.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → empty (exit 0). `__all__` and the re-export list are unchanged. Correct per Decision 14 / build-plan public-export flag: `DjangoConnection` / `DjangoConnectionField` are NOT exported until Slice 4; Slice 1 references the symbols by `connection.py` module path only (the tests import `from django_strawberry_framework.connection import ...`). No drift.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Confirmed: `git diff --stat` shows `docs/GLOSSARY.md` as the only doc change, and its diff is exactly the baseline-dirty Revision-3 `Meta.connection` anchoring (Index row `planned for 0.0.9`, "Type generation"/"Relay" browse rows, and the `## Meta.connection` entry body — all `planned for 0.0.9`, no `shipped` flip). That is the maintainer's carried baseline per the build plan, NOT a Slice 1 edit, and Slice 1 did not touch it further. CHANGELOG.md / README.md / docs/README.md / docs/TREE.md / KANBAN.md / TODAY.md untouched.

### What looks solid

- **Count semantics are spec-faithful and verified end-to-end.** `test_total_count_counts_post_filter_pre_slice_when_selected` proves `first: 1` slices `edges` to one while `totalCount` reflects the full pre-slice count — the Decision 4(c) "post-filter pre-slice" contract. The sync `.count()` / async `.acount()` split (`_attach_count_sync` / `_attach_count_async`) correctly handles `ListConnection.resolve_connection`'s sync-instance-vs-async-coroutine return; I verified against the installed `strawberry/relay/types.py` that the coroutine branch fires only for an async iterable in an async context, and `inspect.isawaitable(conn)` is the right discriminator.
- **Selection-gating is real, per-query (not type-wide), and unit + integration tested.** `_total_count_requested` walks `info.selected_fields` recursively, descends `FragmentSpread.selections` (so `totalCount` inside a named fragment is still found), and correctly excludes `InlineFragment` from the `.name` check. `test_total_count_not_counted_when_not_selected` proves the same schema runs no count when `totalCount` is omitted and the real count when it is selected.
- **`types.new_class` is the correct primitive** for subclassing the parametrized generic `DjangoConnection[target_type]` (the plan's `type(...)` sketch would `TypeError`); the small drift is well-documented and the bare path correctly returns the generic alias (asserted via `__origin__`, since an alias is not a class).
- **Validation failure modes are all pinned** — non-dict, unknown sub-key, non-bool `total_count`, and non-Relay type each raise `ConfigurationError` with a targeted `match=`; the bonus `test_meta_connection_non_bool_total_count_raises` exceeds the plan's three named failures, and `test_meta_connection_absent_leaves_definition_none` pins the default. `ALLOWED_META_KEYS` membership + `DEFERRED_META_KEYS` non-membership asserted.
- **Hotspots did not worsen.** `__init_subclass__` (+1 kwarg, no branch) and `_validate_meta` (+1 straight-line call, no branch) stay as planned; the new branching lives in the small `_validate_connection` helper. `definition.py`'s `connection` slot adds no logic.

### Temp test verification

No temp test files were written under `docs/builder/temp-tests/slice-1/`. The two suspicions (M1 non-null violation, L1 double-guard) were verified with throwaway inline `uv run python -c` schema-build snippets and an MRO dump, not committed test files — nothing to dispose of. M1's reproduction is recorded inline above; Worker 2 should promote a permanent Slice-2 test for it once the Decision 7 resolution is chosen (see Notes for Worker 1).

### Notes for Worker 1 (spec reconciliation)

- **Escalated (M1): Decision 7 does not cover `totalCount`-selected over a non-QuerySet consumer-resolver return.** The count helpers landed in Slice 1 produce a `Cannot return null for non-nullable field ...totalCount` engine error (reproduced) when a consumer `resolver=` returns a non-QuerySet iterable and the query selects `totalCount`. Decision 7 (spec lines 277-283) only specifies the `filter:`/`orderBy:`-against-non-queryset → `GraphQLError` path. Resolution paths for Worker 1 to choose between, to be implemented/tested in Slice 2:
  1. Treat `totalCount` like sidecar input — supplying/selecting it against a non-queryset consumer return raises a clear package `GraphQLError` (symmetric with the filter/order rule), OR
  2. Make `totalCount` resolve to `null` gracefully for non-countable sources (would require the field be `Int` not `Int!` — a schema-shape change conflicting with the `Int!` the SDL currently renders and the User-facing-API `totalCount: Int!` shape), OR
  3. Document that `totalCount` opt-in requires a QuerySet-returning resolver and rely on the engine error (weakest; the message is not package-authored).
  Recommendation: path 1 (clear package error, symmetric with Decision 7's existing non-queryset rule). This needs a one-line Decision 7 (or Edge cases) addition; flagging because Worker 2 cannot edit the spec. Not a Slice 1 blocker — unreachable through Slice 1's own surface.
- **`types.new_class` vs `type(...)` (informational).** Worker 2 recorded this small drift; confirmed correct and within the slice contract. The spec/plan need no edit unless you want to name the primitive.
- **No production cache-clear hook (informational).** The module-level `_connection_type_cache` is cleared only in the test fixture; production never calls `registry.clear()`. Confirmed acceptable for Slice 1. If Slice 4's live usage interacts with a finalization re-run, revisit whether `registry.clear()` should also clear the connection cache; flagging so it is not assumed delivered.
- **L1/L2 (informational, not blocking).** The double-guard execution and the dual `total_count` annotation source are polish items recorded above; neither needs spec context. Worker 1 may direct Worker 2 to address them in Slice 2's `connection.py` pass (same module) rather than re-opening Slice 1.

### Review outcome

`review-accepted`. No High findings. M1 is a real cross-slice seam but is unreachable through Slice 1's own surface (no field factory yet) and its resolution requires Decision 7 spec context Worker 2 cannot provide — escalated to Worker 1 per BUILD.md (transparent Medium escalation), with resolution paths. L1/L2 are non-blocking polish recorded for the Slice-2 `connection.py` pass. Every Slice 1 spec sub-check (checklist lines 103-107) landed in the diff with matching tests; no over-ticks, no silently-unaddressed boxes. DRY is clean — `_validate_connection` reuses the validator template, the definition slot pattern is exact, and the guard literal is single-sited.

---

## Final verification (Worker 1)

Fresh subagent pass. Re-read AGENTS.md / START.md / BUILD.md / worker-1.md, GOAL.md / GLOSSARY.md / CHANGELOG.md, the active spec (Slice 1 checklist + Decisions 3/4/7/8), the active build plan, the full slice artifact (Plan + Build report + Review), and worker-1 memory. Read the working-tree diff under verification directly (`connection.py`, `types/base.py`, `types/definition.py`, `tests/test_connection.py`, `tests/types/test_base.py`).

### Spec slice checklist audit (Worker 1 is no longer the original ticker)

Audited every `- [x]` in the Plan's `### Spec slice checklist (verbatim)` against the diff. All five landed with matching implementation — no over-ticks, no silently un-ticked boxes:

- [x] **`connection.py` + `DjangoConnection[NodeType]` + `first`+`last` guard** — landed. `connection.py::DjangoConnection` subclasses `relay.ListConnection[NodeType]`, carries no `total_count`, and `resolve_connection` calls `_guard_first_and_last(first, last)` (raises `GraphQLError`, not `ConfigurationError`) then delegates to super. Verified.
- [x] **Cached `_connection_type_for(target_type)`** — landed. `connection.py::_connection_type_for` reads `definition.connection`, returns the bare `DjangoConnection[target_type]` generic alias when not opted in, or the generated `<TypeName>Connection` (`_build_total_count_connection` via `types.new_class`) when opted in; cached on `target_type` identity. Verified.
- [x] **`total_count` resolver reads a private instance attr; counts post-filter pre-slice, selection-gated** — landed. `_TOTAL_COUNT_ATTR` private attr, `_total_count_requested(info)` selection walk, `_attach_count_sync`/`_attach_count_async` count the pre-slice `nodes` (`.count()`/`.acount()`) only when selected, then super slices. Verified.
- [x] **`ALLOWED_META_KEYS += "connection"` + `_validate_connection` + stored on `DjangoTypeDefinition`** — landed. `types/base.py` adds `"connection"` to `ALLOWED_META_KEYS` (NOT `DEFERRED_META_KEYS`), `_validate_connection` (dict / unknown-subkey / bool / Relay-Node checks), threaded through `_ValidatedMeta` + `_validate_meta`, stored via `connection=validated.connection` on the single `DjangoTypeDefinition(...)` call; `definition.py` adds the `connection: dict | None = None` slot + Invariants docstring bullet. Verified.
- [x] **Package coverage in `tests/test_connection.py` + `tests/types/test_base.py`** — landed. 14 connection tests + 7 base tests, all covering the named contracts (shape, guard, generation/caching, present-only-opted-in, counted-only-selected, validation failure modes, definition storage). Verified.

No remaining `- [ ]` boxes; no deferral reasons needed.

### DRY check

Clean for this slice — no new duplication vs the validator template or the definition-slot pattern:

- `_validate_connection` reuses the `_validate_filterset_class` / `_validate_orderset_class` template shape (`None`-short-circuit, `ConfigurationError(f"{meta.model.__name__}.Meta.connection …")` sibling tone) but the body is genuinely different (dict / unknown-subkey / bool / Relay-Node), not a copy. The Relay-Node check correctly reuses the `issubclass(i, relay.Node)` half of `_is_relay_shaped` rather than threading `cls` (unusable at `_validate_meta` time) — the plan's one intentional partial-reuse, justified.
- The `connection` slot reuses the `DjangoTypeDefinition` slot pattern exactly (alongside `filterset_class` / `orderset_class`, single store kwarg, zero new `__init_subclass__` branches).
- The `first`+`last` guard literal is single-sited in `_guard_first_and_last`; Strawberry owns cursor / `pageInfo` / slice math via `super().resolve_connection(...)`. No hand-rolled window.
- Repeated `"total_count"` literal (3 semantically-distinct sites in `connection.py`: Meta sub-key read, Python field annotation, resolver name) is below the action threshold for Slice 1; carried to the integration pass to watch if Slice 2 adds more sites. Concur with Worker 3.

### Existing tests still pass

`uv run pytest tests/test_connection.py tests/types/test_base.py --no-cov` → **92 passed in 1.64s** (the `--no-cov` is required — `pytest.ini` `addopts` auto-applies `--cov`; no other coverage flag used). PASS.

### Spec reconciliation — M1 resolved (spec edited)

Worker 3 escalated M1 (Medium): the generated `<TypeName>Connection.totalCount` renders `Int!`, but the count is attached only when `nodes` is a `QuerySet` (`_attach_count_sync` / `_attach_count_async` guard on `isinstance(nodes, models.QuerySet)`). When a consumer `resolver=` returns a non-QuerySet iterable AND `totalCount` is selected, the resolver returns `None` into `Int!` → the engine's `Cannot return null for non-nullable field …totalCount` violation. Decision 7 covered the `filter:`/`orderBy:`-over-non-queryset → `GraphQLError` path but was silent on `totalCount`. The gap is unreachable through Slice 1's surface (no field factory until Slice 2) and becomes live in Slice 2.

**Decision (Worker 1, the only worker who may edit the spec): resolution path 1 — a clear package `GraphQLError`, symmetric with Decision 7's existing non-queryset rule.** Rationale: path 2 (make `totalCount` nullable) conflicts with the `totalCount: Int!` SDL the slice renders and the User-facing-API contract; path 3 (rely on the engine error) leaves a non-package-authored message — the weakest, and against AGENTS.md's root-cause-over-surface-patch standard. Path 1 makes the count helper raise rather than skip-and-return-`null`, keeping the `Int!` shape and giving a clear package error. This is the highest-quality fix and is symmetric with the sidecar-input rule the spec already pins. Slice 2 must implement + test it. See `### Spec changes made (Worker 1 only)` below for cited spec lines.

### L1 / L2 disposition

Both are non-blocking Low polish items in `connection.py` — carried forward to the **Slice 2 `connection.py` pass** (Slice 2 re-touches that exact module), per Worker 3's note that neither needs spec context:

- **L1 — `first`+`last` guard executes twice on the opted-in path** (the generated `resolve_connection` calls `_guard_first_and_last` then super-chains into `DjangoConnection.resolve_connection` which guards again). Idempotent / harmless; recorded for Slice 2 to either drop the explicit call or add an intentional-defensiveness comment.
- **L2 — `total_count` field carries two annotation sources with mismatched nullability** (`__annotations__ = {"total_count": int}` wins → `Int!`, but the resolver is typed `-> int | None`). Behavior is correct; recorded for Slice 2 to align the resolver return type (`-> int`) once M1's path-1 raise lands (after M1, the QuerySet-only count path makes `int` honest).

These are recorded here and in worker-1 memory so the Slice 2 planning pass picks them up; they are NOT Slice 1 blockers (no source/test edit by Worker 1).

### Public-surface / version / CHANGELOG / GLOSSARY guards

- `git diff HEAD -- django_strawberry_framework/__init__.py` → empty. `__all__` / re-export list unchanged (correct per Decision 14 — exports land in Slice 4).
- `git diff HEAD -- pyproject.toml tests/base/test_init.py uv.lock` → empty. No version-file edits (correct per Decision 13; on-disk version stays `0.0.8`).
- `git diff HEAD -- CHANGELOG.md` → empty. Untouched (correct — CHANGELOG edit is Slice 5 only).
- `docs/GLOSSARY.md` → unchanged by this pass; the working-tree diff is exactly the carried baseline-dirty Revision-3 `Meta.connection` anchoring (21 insertions / 2 deletions, all `planned for 0.0.9`). NOT reverted, NOT altered by Slice 1 or by final verification. Correct.

### Spec status-line re-verification

The spec header line 5 read `Status: planned — no slice started`, which is stale now that Slice 1 has built / reviewed / accepted. Updated to `Status: in build — Slice 1 accepted` (the five-slice enumeration after it is still accurate descriptive content). Recorded under `### Spec changes made (Worker 1 only)`. The Slice checklist boxes in the spec stay unticked by design (spec line 3: build progress is tracked in the build plan, not the spec).

### Summary

Slice 1 ships the `DjangoConnection[T]` Relay-connection base (a `strawberry.relay.ListConnection` subclass owning the package's `first`+`last` `GraphQLError` guard that Strawberry's `SliceMetadata.from_arguments` omits), the cached `_connection_type_for(target_type)` factory that returns the bare generic alias for non-opted types and a generated concrete `<TypeName>Connection` (via `types.new_class`) carrying a selection-gated, post-filter-pre-slice `totalCount` (sync `.count()` / async `.acount()`, attached per connection instance) for `total_count`-opted types, and the net-new `Meta.connection` key — added directly to `ALLOWED_META_KEYS`, shape-validated by `_validate_connection` (dict / `{"total_count": bool}`-only / Relay-Node-required), and stored on `DjangoTypeDefinition.connection` for the factory to read. 14 connection tests + 7 base tests pin the surface; focused suite is green (92 passed). No public-surface, version, CHANGELOG, or baseline-GLOSSARY drift. M1 resolved by a Decision 7 spec edit (path 1, clear package `GraphQLError` for `totalCount`-over-non-queryset) for Slice 2 to implement; L1/L2 carried to the Slice 2 `connection.py` pass.

### Spec changes made (Worker 1 only)

All edits to `docs/spec-030-connection_field-0_0_9.md`, triggered by Slice 1 (the M1 escalation + the per-spawn status-line check):

- **Decision 7, consumer-`resolver=` contract paragraph (`docs/spec-030-connection_field-0_0_9.md` #"The same non-queryset incompatibility extends to `totalCount`")** — extended the contract so that selecting `totalCount` against a non-`QuerySet` consumer-resolver return on a `total_count`-opted-in type raises a clear package `GraphQLError` (the count helper raises rather than returning `null` into `Int!`). Reason: resolve escalated M1 via path 1, symmetric with the existing sidecar-input non-queryset rule; Slice 2 implements + tests it.
- **Error shapes section (`docs/spec-030-connection_field-0_0_9.md` #"`totalCount` selected against a consumer resolver that returned a non-queryset iterable")** — added a bullet pinning the same `GraphQLError` shape. Reason: keep the Error-shapes list complete and consistent with the Decision 7 edit.
- **Edge cases section (`docs/spec-030-connection_field-0_0_9.md` #"Consumer `resolver=` returns a non-queryset iterable while `totalCount` is selected")** — added an edge-case bullet for the same case. Reason: internal consistency with the existing non-queryset-with-sidecar-input edge case.
- **Slice 2 Test plan (`docs/spec-030-connection_field-0_0_9.md` #"test_consumer_resolver_iterable_with_total_count_selected_raises")** — added the Slice 2 test bullet for the new contract. Reason: ensure Slice 2 ships a test that the `totalCount`-over-non-queryset path raises a clear package `GraphQLError` (not the engine non-null violation).
- **Status header line 5 (`docs/spec-030-connection_field-0_0_9.md` #"Status: in build — Slice 1 accepted")** — flipped `Status: planned — no slice started` → `Status: in build — Slice 1 accepted`. Reason: per-spawn spec status-line re-verification (worker-1.md); the prior line was stale now that Slice 1 has built / reviewed / accepted.

No other spec edits. No source/test edits by Worker 1.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[connection]: ../../django_strawberry_framework/connection.py
[definition]: ../../django_strawberry_framework/types/definition.py

<!-- tests/ -->
[test-connection]: ../../tests/test_connection.py
[test-types-base]: ../../tests/types/test_base.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[strawberry-relay]: https://strawberry.rocks/docs/guides/relay
