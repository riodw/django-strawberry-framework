# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## DRY analysis

- **Existing patterns reused.** `_get_context_value` (`django_strawberry_framework/optimizer/_context.py:45-87`) is the single read seam the file uses for all three optimizer-stashed context keys (`DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`, `DST_OPTIMIZER_STRICTNESS`); the symmetric write side lives at `optimizer/extension.py:635-644`, exactly the "load-bearing parallels" pattern flagged in `worker-memory/worker-1.md`. `resolver_key` / `runtime_path_from_info` (`optimizer/plans.py:140-149,152-162`) are the canonical branch-sensitive-key constructors, reused identically from `optimizer/walker.py:366,518-519`. `FieldMeta.from_django_field` (`optimizer/field_meta.py:113-170`) is the canonical Django→FieldMeta builder used in `_field_meta_for_resolver`'s registry-miss branch (`types/resolvers.py:182`). `is_many_side_relation_kind` (`utils/relations.py:68-70`) backs both `FieldMeta.is_many_side` (`optimizer/field_meta.py:108-111`) and the `_check_n1` cache dispatch (`types/resolvers.py:139`). `registry.get_definition` (`registry.py`) + `DjangoTypeDefinition.field_map` (`types/definition.py:50`) are read at `_field_meta_for_resolver:165-167` exactly per the inter-module contract described at `optimizer/field_meta.py:3-17` ("Every consumer of relation cardinality + nullable + attname should read from a FieldMeta instance via DjangoTypeDefinition.field_map or a fresh FieldMeta.from_django_field call"). `_attach_relation_resolvers` is called exactly once from `types/finalizer.py:218-222` Phase 2, with `definition.consumer_assigned_relation_fields` (`types/definition.py:57`, built at `types/base.py:170-187`). Test coverage spans `tests/types/test_resolvers.py:136-590` covering every cardinality branch, FK-id elision (B2), and N+1 dispatch (B3).
- **New helpers a fix might justify.** A `FieldMeta.from_relation_like(field)` classmethod on `FieldMeta` that mirrors `from_django_field` but accepts a `SimpleNamespace`-shaped descriptor missing `is_relation` (the test-double path) would consolidate the inline `FieldMeta(name=..., is_relation=True, ...)` kwarg block at `types/resolvers.py:171-181` and pick up the same cardinality-gated `nullable` rule `from_django_field` applies at `optimizer/field_meta.py:153-156`. Single call site today (`types/resolvers.py:170-181`), so it's a Medium DRY candidate, not a build-now requirement; the asymmetry it would close is documented under Medium M1 below.
- **Duplication risk in the current file.** The three nested resolver closures (`many_resolver`, `reverse_one_to_one_resolver`, `forward_resolver`) each open with an identical `_check_n1(info, root, field_name, parent_type, kind=kind)` line (`types/resolvers.py:215,224,235`), with the forward branch additionally pre-empting the strictness check on the FK-id-elision short-circuit (lines 233-234). The repetition is intentional — each closure has a distinct tail (`list(...).all()` vs `try/except DoesNotExist` vs `getattr` with elision pre-empt) and centralising the head would force a hot-path branch on `kind` per call. Same-shape calibration as the scalars.py input/output gates / _context.py read-write mirror: load-bearing parallels, not a DRY finding. No repeated string literals (the helper's overview confirms `None.`). One legitimate near-duplicate: the `field_meta.related_model` vs `field.related_model` read in `_make_relation_resolver` (line 221 uses raw `field`, lines 73/78 use canonical `field_meta`) — flagged as Low L2.

## High:

None.

## Medium:

### `_field_meta_for_resolver` fallback FieldMeta drifts from `FieldMeta.from_django_field`'s nullable rule and omits target-column attrs

When the parent type is unregistered (or the field is missing from `field_map`), `_field_meta_for_resolver` builds a `FieldMeta` by hand at `types/resolvers.py:171-181`. The constructed record:

- reads `nullable=bool(getattr(field, "null", False))` directly (line 177), skipping the cardinality gate `FieldMeta.from_django_field` enforces at `optimizer/field_meta.py:153-156` (forward M2M / reverse FK → `False`; reverse OneToOne → `True`; else follows `field.null`). For a test double simulating a reverse-FK shape (`one_to_many=True`, `auto_created=True`, no `null` attribute), the canonical builder forces `nullable=False`; this fallback returns `False` by getattr default which happens to agree, but a double with `null=True` on a many-side shape would advertise `nullable=True` — wrong per the documented contract;
- omits `target_field_name`, `target_field_attname`, and `reverse_connector_attname` (lines 171-181 vs `optimizer/field_meta.py:166-168`). Resolvers don't read those fields today, but `FieldMeta`'s docstring (`optimizer/field_meta.py:7-9`) says it is the *canonical* single source of truth for "FK target columns" across the package; a fallback that quietly drops them is the same "advertised contract vs runtime reality" Medium-tier pattern recorded in `worker-memory/worker-1.md` (converters.py / extension.py / plans.py).

The `if not hasattr(field, "is_relation"):` guard exists exclusively for test doubles per the docstring at `types/resolvers.py:90-91` ("compatibility for test doubles"). The cleaner shape is to either (a) require test doubles to expose `is_relation` and use `FieldMeta.from_django_field` uniformly, or (b) add a `FieldMeta.from_relation_like(field)` classmethod that reuses the cardinality-gated nullable rule and target-column reads from the canonical builder. Today's inline-build keeps the production path correct (registered types always hit the `field_map.get` short-circuit at line 167) but the test-double surface is the same FieldMeta the optimizer walker would read off `field_map`, so silent drift here is exactly the kind of "test exercises a different shape than production" trap the package's canonical-builder discipline was meant to close.

```django_strawberry_framework/types/resolvers.py:162:182
def _field_meta_for_resolver(field: Any, parent_type: type | None) -> FieldMeta:
    """Return registered ``FieldMeta`` for ``field`` when the parent type exposes it."""
    if parent_type is not None:
        definition = registry.get_definition(parent_type)
        if definition is not None:
            meta = definition.field_map.get(field.name)
            if meta is not None:
                return meta
    if not hasattr(field, "is_relation"):
        return FieldMeta(
            name=field.name,
            is_relation=True,
            many_to_many=bool(getattr(field, "many_to_many", False)),
            one_to_many=bool(getattr(field, "one_to_many", False)),
            one_to_one=bool(getattr(field, "one_to_one", False)),
            nullable=bool(getattr(field, "null", False)),
            related_model=getattr(field, "related_model", None),
            attname=getattr(field, "attname", None),
            auto_created=bool(getattr(field, "auto_created", False)),
        )
    return FieldMeta.from_django_field(field)
```

### `_check_n1` legacy-default `kind=None` path silently mis-dispatches many-side under fakeshop test doubles

`_check_n1`'s `kind` parameter defaults to `None`, and the contract at `types/resolvers.py:127-130` says "when `kind` is `None` (legacy direct calls in tests), the function falls back to the single-valued cache check, which is the conservative shape that used to be the only branch." But `_make_relation_resolver` always closes over `kind = field_meta.relation_kind` (line 210) and passes it through, so the only `None`-default consumers are direct test calls. Two of those direct tests (`tests/types/test_resolvers.py:355-376` `test_check_n1_ignores_bare_field_name_key`, `tests/types/test_resolvers.py:378-396` `test_check_n1_returns_when_relation_is_already_loaded`) exercise the `kind=None` legacy path, but every newer test (lines 421-542) passes `kind=` explicitly. Two issues:

1. The branch is exercised but its risk is opposite to what the docstring claims. The "conservative shape" comment frames `_will_lazy_load_single` as the safer fallback. For a *many-side* relation the single-valued check reads `root.__dict__` (`types/resolvers.py:93`) which a test double populating `root.items = [...]` would short-circuit, silently *exempting* a real many-side lazy-load case from strictness. That's the exact failure mode `test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy` (`tests/types/test_resolvers.py:493-521`) was added to pin against — but only on the `kind="many"` / `kind="reverse_many_to_one"` path. The `kind=None` default leaves the legacy escape hatch open.
2. The legacy default is dead in production. `_make_relation_resolver` is the only production caller (via the three closures at lines 214/223/232) and always supplies `kind`. Test-only API surface is the textbook "code only the tests reach" Medium per `worker-memory/worker-1.md` "Dead-code-but-public" calibration.

Recommended change: make `kind` keyword-only and required (`*, kind: str | None`); update the two direct-test call sites to pass `kind=None` explicitly when they want the legacy single-valued path, or pass the correct shape when they want the strict path. Pin the contract with a docstring rewrite that names "`kind` is required" and explains why the absence of `kind` is a programming error in newly-written tests.

```django_strawberry_framework/types/resolvers.py:115:131
def _check_n1(
    info: Any,
    root: Any,
    field_name: str,
    parent_type: type | None = None,
    *,
    kind: str | None = None,
) -> None:
    """B3: warn or raise if the relation is not planned and would lazy-load.

    ``kind`` accepts the ``relation_kind`` of the field being resolved.
    ``"many"`` and ``"reverse_many_to_one"`` use the many-side cache
    check; every other known relation shape uses the single-valued cache
    check. When ``kind`` is ``None`` (legacy direct calls in tests), the
    function falls back to the single-valued cache check, which is the
    conservative shape that used to be the only branch.
    """
```

## Low:

### L1 — `_resolver_logger` import re-uses the optimizer package logger via re-export

`_resolver_logger = ..optimizer.logger` (`types/resolvers.py:30`) borrows the optimizer subpackage's logger object so the N+1 warning at line 149 lands under the `django_strawberry_framework` namespace consumers configure. That works (test pins use `caplog.set_level("WARNING", logger="django_strawberry_framework")` at `tests/types/test_resolvers.py:415`), but it means `types/resolvers.py` depends on a re-exported attribute on `..optimizer.__init__.py` instead of going through `logging.getLogger("django_strawberry_framework")` directly. The current shape is fine; the recommended polish is either (a) document the cross-package logger sharing in the module docstring so future readers don't replace it with a fresh `getLogger` call, or (b) define the logger locally and let both modules sit on the same name. Low because no behavior risk.

```django_strawberry_framework/types/resolvers.py:30
from ..optimizer import logger as _resolver_logger
```

### L2 — `field.related_model.DoesNotExist` reads the raw field after canonicalising via FieldMeta

At `types/resolvers.py:221`, the reverse-OneToOne branch reads `field.related_model.DoesNotExist`, while the surrounding code uses `field_meta.related_model` (lines 73, 78) and `field_meta.one_to_one`/`field_meta.auto_created` (line 220) for the discriminator. `FieldMeta` is documented as the canonical source for `related_model` (`optimizer/field_meta.py:7`), so the asymmetric raw-field read sits oddly next to the canonical reads above and below it. Behavior is identical (a real reverse-OneToOne descriptor's `related_model` matches `field_meta.related_model`), so this is convention polish only. Recommended change: `related_does_not_exist = field_meta.related_model.DoesNotExist`. Low.

```django_strawberry_framework/types/resolvers.py:220:221
    if field_meta.one_to_one and field_meta.auto_created:
        related_does_not_exist = field.related_model.DoesNotExist
```

### L3 — `parent_type: type | None = None` default in `_make_relation_resolver` and `_field_meta_for_resolver` is test-only surface

`_attach_relation_resolvers` always passes `parent_type=cls` (`types/resolvers.py:260`), so the `None` default exists only for the four direct unit tests at `tests/types/test_resolvers.py:143,168,577` and the one `_field_meta_for_resolver` legacy fallback. Same shape as the `_check_n1 kind=None` Medium, downgraded to Low because the registry-miss branch is also reachable in production when a SimpleNamespace-shaped synthetic field is passed without registry registration (e.g., during partial type setup), so the default value carries some legitimate weight. Recommended polish only: a short docstring line on each saying "the `None` default exists for test-double direct calls; production calls always supply `parent_type=cls`."

```django_strawberry_framework/types/resolvers.py:185:185
def _make_relation_resolver(field: Any, parent_type: type | None = None) -> Any:
```

### L4 — `_name_resolver` mutates `resolver.__name__` after the closure is built

`_name_resolver` writes `resolver.__name__ = f"resolve_{field_name}"` (`types/resolvers.py:158`). For a `def` closure this is safe (function attributes are writable), but the helper accepts `Any` so a hypothetical callable that disallows `__name__` writes would surface a late `AttributeError`. Real production callables are all module-local `def`s (lines 214, 223, 232); the typing is just looser than needed. Recommended polish: tighten the signature to `Callable[..., Any]` and add a one-line docstring note that the helper assumes a Python-function callable. Low.

```django_strawberry_framework/types/resolvers.py:152:159
def _name_resolver(resolver: Any, field_name: str) -> Any:
    """Stamp ``resolver.__name__`` to ``resolve_<field_name>``.

    Keeps GraphiQL traces readable and centralises the three
    cardinality-branch rename calls in ``_make_relation_resolver``.
    """
    resolver.__name__ = f"resolve_{field_name}"
    return resolver
```

### L5 — `_EMPTY_FROZENSET` sentinel applies only to the FK-id-elision read

The module-level `_EMPTY_FROZENSET` sentinel at `types/resolvers.py:46` is used exactly once at `_is_fk_id_elided:60` to avoid allocating a fresh empty frozenset per call when the optimizer has not stashed elisions. The same allocation-avoidance lesson does NOT apply to the `_check_n1` read at line 133 (it uses `default=None` and short-circuits via the `if planned is None: return` branch on line 134 — the sentinel isn't a hot-path saver there). Low polish: rename the constant to `_EMPTY_ELISIONS` to pin the single-purpose use, or document why the same shape isn't applied to the other two `_get_context_value` calls in the file (lines 133, 145). Today the comment at lines 44-45 explains the allocation rationale but does not explain why the other reads don't need the same treatment.

```django_strawberry_framework/types/resolvers.py:44:46
# Module-level immutable sentinel for the "no elisions registered" branch so
# the forward-resolver dispatch does not allocate a fresh empty set per call.
_EMPTY_FROZENSET: frozenset[str] = frozenset()
```

## What looks solid

- Static helper ran cleanly (`docs/shadow/django_strawberry_framework__types__resolvers.overview.md`); only one control-flow hotspot (`_make_relation_resolver`, 54 lines / 3 branches), no repeated string literals, no TODO comments.
- Symmetric read/write seam with `optimizer/_context.py`'s `get_context_value` / `stash_on_context` and the four `DST_OPTIMIZER_*` constants — this file consumes exactly what `optimizer/extension.py:635-644` produces, and the cross-module contract is the documented load-bearing parallel (sentinel-discipline + symmetric-helpers pattern from `worker-memory/worker-1.md`).
- Single-direction dependency on `optimizer/` (this module reads optimizer-built records but writes nothing back); no circular-import risk; module-docstring at `types/resolvers.py:16-21` explicitly explains the sibling-of-`types.base` layering for the same reason.
- Test coverage is comprehensive across every cardinality branch and every strictness/elision dispatch (`tests/types/test_resolvers.py:136-590` — 14 direct unit tests covering many-side, reverse OneToOne `DoesNotExist`-to-None, forward FK-id elision with stub building, parent-type isolation, bare-key rejection, prefetch-cache recognition, and the four strictness modes).
- Branch-sensitive resolver-key dispatch (parent type + runtime path tuple) is correctly threaded from the optimizer write side (`optimizer/walker.py:366,518-519`) to the resolver read side (`types/resolvers.py:62,136`) using the exact same `resolver_key` / `runtime_path_from_info` helpers — no string-key drift between writer and reader.
- `_will_lazy_load_single` vs `_will_lazy_load_many` is the right split for cache discipline; the asymmetric "no `__dict__` short-circuit on the many side" decision is explicitly documented at lines 105-109 and test-pinned at `tests/types/test_resolvers.py:493-521`.
- `_build_fk_id_stub` correctly stamps `_state.adding = False` and `_state.db = router.db_for_read(...)` so the synthesized stub does not accidentally trigger a save or sit on a stale DB alias; pinned at `tests/types/test_resolvers.py:200-210`.

### Summary

`types/resolvers.py` is the resolver-side read of the optimizer-stashed context contract, well-layered as a sibling of `types/base` to avoid circular imports, and it correctly reuses every shared helper (`_get_context_value`, `resolver_key`, `runtime_path_from_info`, `FieldMeta.from_django_field`, `is_many_side_relation_kind`). The two Medium findings (M1 `_field_meta_for_resolver` fallback FieldMeta drift from the canonical builder; M2 `_check_n1` legacy `kind=None` default is now dead in production and silently bypasses the many-side cache discipline) are both "test-double path drifts from the production canonical path" — the same calibration `worker-memory/worker-1.md` records as "advertised contract vs runtime reality" Medium-tier patterns. No High-severity findings; no DRY duplication beyond the load-bearing per-cardinality closure shape. Carry-forward for the folder pass: the `field_meta` thread-through asymmetry the `rev-types__finalizer.md` artifact flagged for `resolved_relation_annotation` is the same shape as M1 here (canonical FieldMeta builder vs inline kwargs) — confirm at folder pass that no fourth sibling does the same.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/resolvers.py`:
  - M1: `_field_meta_for_resolver` test-double fallback now mirrors the cardinality-gated nullable rule and target-column reads from `FieldMeta.from_django_field` (optimizer/field_meta.py:135-170). Many-side cardinalities short-circuit to `nullable=False`, reverse-OneToOne short-circuits to `True`, every other single-relation shape follows `field.null`. Adds `target_field_name`, `target_field_attname`, and `reverse_connector_attname` reads. Imports `relation_kind` from `..utils.relations`. Inline path retained (not extracted into a `field_meta.py` helper) per dispatch's "simpler path" instruction.
  - M2: `_check_n1` `kind` is now keyword-only and required (no default). Docstring rewritten to say `kind` is required and to frame `kind=None` as an explicit legacy opt-in. The two test-only callers that used the legacy default now pass `kind=None` explicitly; one (`test_check_n1_warns_for_unplanned_lazy_load`) also previously omitted `kind` and was updated.
  - L2: reverse-OneToOne `DoesNotExist` read now goes through `field_meta.related_model.DoesNotExist` instead of `field.related_model.DoesNotExist`, matching the canonical-`FieldMeta` reads above and below in the same function.
  - L4: `_name_resolver` signature tightened from `(Any, str) -> Any` to `Callable[..., Any]` shape; docstring notes the helper assumes a Python-function callable with a writeable `__name__`. Ruff moved the `Callable` import to `collections.abc` after the edit.
  - L5: `_EMPTY_FROZENSET` renamed to `_EMPTY_ELISIONS`; comment retained (already explains the allocation-avoidance rationale).
- `tests/types/test_resolvers.py`:
  - `test_check_n1_ignores_bare_field_name_key` (line 355): added `kind=None` keyword arg to the `_check_n1` call.
  - `test_check_n1_returns_when_relation_is_already_loaded` (line 378): added `kind=None` keyword arg.
  - `test_check_n1_warns_for_unplanned_lazy_load` (line 398): added `kind=None` keyword arg (was previously relying on the now-removed default).

### Tests added or updated

- No new tests added. M1 mirrors the canonical builder's behavior (no observable behavior change for any field shape the existing tests exercise); M2 is an API tightening covered by the three existing direct unit tests that now pass `kind=None` explicitly; L2/L4/L5 are pure convention/naming polish.

### Validation run

- `uv run ruff format .` — pass (101 files left unchanged).
- `uv run ruff check --fix .` — pass (2 auto-fixes applied: `Callable` import relocated to `collections.abc`; 0 remaining errors).
- `uv run pytest tests/types/test_resolvers.py -x` — 23 passed in 0.96s. (Coverage failure at the focused-run level is expected — coverage gate is for the full suite.)

### Notes for Worker 3

- M1 inline-build path is reachable today only by the three `SimpleNamespace`-based direct unit tests in `tests/types/test_resolvers.py:136-176` (no real production call site hits the `not hasattr(field, "is_relation")` branch — production fields always have `is_relation`, and the registry-shortcut at lines 169-174 wins first when the type is registered). The behavior shift from the inline-build change is: a test double advertising `null=True` on a many-side shape would previously return `nullable=True`; it now returns `nullable=False`. No existing test exercises that exact combination, so no test was added/changed for it.
- M2 is a signature tightening; the three test call sites updated to add `kind=None` are the only direct test consumers. Worker 1's review artifact explicitly flagged the legacy `kind=None` default as "test-only API surface" and recommended exactly this change; the docstring rewrite matches the recommendation's "kind is required" framing.
- L2 / L4 / L5 are pure convention/naming polish with no behavior change. The `Callable` import landed under `collections.abc` (ruff auto-fixed from `typing` per the project's `from __future__` / PEP 585 style) — both forms are equivalent at runtime.
- Comment pass and changelog disposition deferred to a later pass per dispatch instructions.

---

## Verification (Worker 3)

### Logic verification outcome

_pending_

### DRY findings disposition

_pending_

### Temp test verification

_pending_

### Verification outcome

_pending_

## Verification (Worker 3)

- M1 accepted: `_field_meta_for_resolver` fallback now mirrors `FieldMeta.from_django_field`'s cardinality-gated nullable rule (many-side → `False`; reverse-OneToOne → `True`; else `field.null`) via the imported `relation_kind` helper, and adds `target_field_name`, `target_field_attname`, and `reverse_connector_attname` reads off `target_field`/`field.field`. The inline-build shape was retained per dispatch's "simpler path" instruction rather than extracting a new `field_meta.py` helper; this matches the artifact's option (a)/(b) framing and the Fix report's stated choice.
- M2 accepted: `_check_n1`'s `kind` is now keyword-only and required (`kind: str | None` without default). Docstring rewritten to explicitly frame `kind=None` as the explicit legacy opt-in for the single-valued check and call out absence-of-`kind` as a programming error in new callers. The three direct unit tests that used the legacy default (`test_check_n1_ignores_bare_field_name_key`, `test_check_n1_returns_when_relation_is_already_loaded`, `test_check_n1_warns_for_unplanned_lazy_load`) now pass `kind=None` explicitly.
- L2 accepted: reverse-OneToOne `DoesNotExist` now reads from `field_meta.related_model.DoesNotExist` (line 243), matching the canonical-`FieldMeta` reads above and below in `_make_relation_resolver`.
- L4 accepted: `_name_resolver` signature tightened to `Callable[..., Any] -> Callable[..., Any]`; `Callable` imported from `collections.abc`; docstring note added that the helper assumes a Python-function callable with a writeable `__name__`.
- L5 accepted: `_EMPTY_FROZENSET` → `_EMPTY_ELISIONS`; only call site (`_is_fk_id_elided`) updated.
- L1 deferred to comment pass: re-export-vs-direct `getLogger` framing is comment polish only with no behavior risk; correctly deferred to the comment pass per the artifact's Low rationale.
- L3 deferred to comment pass: `parent_type: type | None = None` default is short docstring polish only; correctly deferred to the comment pass.
- Validation: `uv run pytest tests/types/ -x` → 242 passed, 2 skipped (coverage fail_under is expected on a focused-folder run; full-suite coverage is gated at the final test-run gate per the plan).
- Verification outcome: `logic accepted; awaiting comment pass`.

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/types/resolvers.py`:
  - **L1**: Added a one-line comment above `from ..optimizer import logger as _resolver_logger` (now line 31) explaining the cross-package logger sharing so future readers don't replace it with a fresh `getLogger("django_strawberry_framework")` call. Wording: "Share the optimizer subpackage's logger so consumers configuring \"django_strawberry_framework\" see N+1 warnings." Split over two lines to fit ≤110 cols per project lint.
  - **L3**: Added a one-line docstring note to `_field_meta_for_resolver` (line 167) saying "the `None` default exists for test-double direct calls; production calls always supply `parent_type=cls`." Same note added to `_make_relation_resolver` (line 207).

### Validation run

- `uv run ruff format .` — pass (101 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed; one reformat to land L1 within the 110-col line limit).

### Notes for Worker 3

- L1 wording is the dispatch-suggested phrasing; placed immediately above the `from ..optimizer import logger as _resolver_logger` import rather than in the module docstring because the import line is the maintenance-relevant site (the warning would be "should I replace this with `getLogger`?" at that exact line).
- L3 docstring notes mirror dispatch's exact wording on both `_field_meta_for_resolver` and `_make_relation_resolver`.
- No behavior change. No new imports.

---

## Changelog disposition

**Disposition:** not warranted.

**Reason:** Every change in this cycle is internal-only with no public-API impact:

- **M1** updated `_field_meta_for_resolver`'s test-double fallback to match `FieldMeta.from_django_field`'s canonical builder. Leading underscore → private.
- **M2** made `_check_n1`'s `kind` parameter keyword-only and required. Leading underscore → private; not exposed in `__all__` or in any public re-export.
- **L2** rerouted the reverse-OneToOne `DoesNotExist` read through `field_meta.related_model` instead of the raw `field`. Identical behavior; convention polish only.
- **L4** tightened `_name_resolver`'s signature to `Callable[..., Any]`. Private helper.
- **L5** renamed `_EMPTY_FROZENSET` → `_EMPTY_ELISIONS`. Module-private constant.
- **L1** + **L3** are comment/docstring polish with zero behavior impact.

No public symbol added, removed, or renamed. No production call path changes behavior. Per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" and the absence of an explicit changelog authorization in the active review plan, no `CHANGELOG.md` edit is made.

---

## Iteration log

_pending_

---

## Verification (Worker 3, pass 2)

- L1+L3 accepted; cycle done.
- L1: one-line comment "Share the optimizer subpackage's logger so consumers configuring \"django_strawberry_framework\" see N+1 warnings." now sits immediately above `from ..optimizer import logger as _resolver_logger` at `django_strawberry_framework/types/resolvers.py:32-34`, matching the dispatch-suggested phrasing and pinning the maintenance-relevant site (the warning would arise at the import line, not in the module docstring).
- L3: identical one-line note "The `None` default exists for test-double direct calls; production calls always supply `parent_type=cls`." appended to both `_field_meta_for_resolver` (`django_strawberry_framework/types/resolvers.py:173-174`) and `_make_relation_resolver` (`django_strawberry_framework/types/resolvers.py:217-218`) docstrings; the sole production call site `_attach_relation_resolvers` continues to pass `parent_type=cls` at `django_strawberry_framework/types/resolvers.py:292`.
- Changelog disposition recorded: not warranted; cites both the `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" rule and the active plan's lack of an authorized changelog pass; `git diff -- CHANGELOG.md` is empty.
- Verification outcome: `cycle accepted; verified`.
