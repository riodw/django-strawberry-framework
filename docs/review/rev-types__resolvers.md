# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## DRY analysis

- **Cross-folder mirror `_field_meta_for_resolver` vs `FieldMeta.from_django_field` — owned by the folder pass per dispatch.** The 11-line nullable-rule + 9-attribute `FieldMeta(...)` body at `types/resolvers.py:190-212` line-for-line duplicates `optimizer/field_meta.py::FieldMeta.from_django_field` (`optimizer/field_meta.py:141-164`). Recommended consolidation shape (already enumerated in `rev-optimizer__field_meta.md::## DRY analysis #1`): extract `FieldMeta._from_field_shape(field: Any, *, is_relation: bool) -> FieldMeta` so `from_django_field` becomes guard-then-delegate and `_field_meta_for_resolver`'s fallback collapses to `return FieldMeta._from_field_shape(field, is_relation=True)`. NOT re-filed here as an act-now opportunity at the per-file scope — per the cycle dispatch note, the cross-folder DRY landing is owned by `rev-types.md` (folder pass). Recap-only here so the next DRY cycle does not re-triage it.
- **Defer until a third `resolver_key(...)` site lands inside this file that needs `runtime_path_from_info(info)`.** Both `_is_fk_id_elided` (`types/resolvers.py:66`) and `_check_n1` (`types/resolvers.py:141`) build the same `resolver_key(parent_type, field_name, runtime_path_from_info(info))` 3-tuple from the same three arguments; the closure-captured `parent_type` / `field_name` / `info` triple is the natural input to a `_resolver_key_from_info(parent_type, field_name, info)` thin helper. Today only two call sites exist, and the helper would obscure the `key in elisions` / `key in planned` near-symmetry that the bodies put one line below the build. Trigger: any third site in this file that needs the same key-from-info build (most plausibly an O5-shape "planned writes" mutation hook or a per-field strictness override).

## High:

None.

## Medium:

### GLOSSARY drift on `Strictness mode` — entry says `RuntimeError`, code raises `OptimizerError`

`docs/GLOSSARY.md:1098-1112` ("`Strictness mode`", `Status: shipped (0.0.3)`) documents the public consumer-contract behavior of `DjangoOptimizerExtension(strictness="raise")` as "fail-fast `RuntimeError` for tests / dev checks" (`docs/GLOSSARY.md:1106`). The actual raise at `types/resolvers.py:152` is `raise OptimizerError(f"Unplanned N+1: {field_name}")`, where `OptimizerError` subclasses `DjangoStrawberryFrameworkError` (not `RuntimeError`) per `django_strawberry_framework/exceptions.py:33`. This is a real public-contract surface — consumers writing `try / except RuntimeError` against the GLOSSARY's documented promise would silently miss every unplanned-N+1 strictness incident; consumers writing `try / except OptimizerError` get the right behavior but contradict the documented prose.

The same GLOSSARY already cites the correct exception in another entry: `Multi-database cooperation` at `docs/GLOSSARY.md:750` reads "Strictness-mode N+1 detection is connection-agnostic and surfaces the same `OptimizerError` shape under non-default aliases." Internal inconsistency in the same standing doc — the older `Strictness mode` entry rotted when the raise type narrowed from a bare `RuntimeError` to the typed `OptimizerError` (no GLOSSARY edit shipped alongside the narrowing).

Severity calibration is Medium not Low because the drift is on a `shipped` public-contract entry, the failure mode is "consumers' typed exception handlers silently fail to catch", and the same GLOSSARY contradicts itself two entries away (the inconsistency itself amplifies the drift). Same calibration as `rev-management__commands__export_schema.md::M1` ("Schema export management command" lagging post-`Added` `Changed` / `Fixed` shipped behaviors).

Verbatim replacement prose for `docs/GLOSSARY.md:1098-1112` (Worker 2 lifts directly):

```
## Strictness mode

**Status:** shipped (`0.0.3`).

`DjangoOptimizerExtension(strictness="off" | "warn" | "raise")` controls how the optimizer reacts when an unplanned relation access would actually lazy-load (an accidental N+1).

- `"off"` — silent production default.
- `"warn"` — logged warning per occurrence.
- `"raise"` — fail-fast [`OptimizerError`](#optimizererror) for tests / dev checks.

Warnings and errors fire only when the relation access actually causes a lazy load — false positives from unhit prefetches do not trigger.

Planned resolver keys and lookup paths are stashed on `info.context` for introspection during strictness incidents.

**See also:** [`DjangoOptimizerExtension`](#djangooptimizerextension) · [`OptimizerError`](#optimizererror) · [Schema audit](#schema-audit).
```

The verbatim replacement assumes `rev-exceptions.md`'s forwarded `OptimizerError` GLOSSARY entry lands at the project pass — if the project pass declines that, fall back to plain `` `OptimizerError` `` (un-linked, plain backticks) in the bullet. The "See also" line picks up the new entry once it exists.

```docs/GLOSSARY.md:1106
- `"raise"` — fail-fast `RuntimeError` for tests / dev checks.
```

```django_strawberry_framework/types/resolvers.py:150-152
        strictness = _get_context_value(context, DST_OPTIMIZER_STRICTNESS, "off")
        if strictness == "raise":
            raise OptimizerError(f"Unplanned N+1: {field_name}")
```

## Low:

### `_check_n1` docstring frames `kind=None` as "programming error" but production tests pin `kind=None` as the documented test-double fallback

`types/resolvers.py:131-135` says: "Pass `kind=None` only when you explicitly want the legacy single-valued check — the absence of `kind` in a new caller is a programming error, since production `_make_relation_resolver` always supplies the relation kind." The shipped test suite at `tests/types/test_resolvers.py:284`, `:301`, `:319` pins three call sites that pass `kind=None` from `_check_n1` directly without going through `_make_relation_resolver` — these are the "legacy single-valued check" path the docstring names, and they are part of the pinned contract today (not regressions).

The phrase "programming error" reads as if `kind=None` is unsupported / will be removed; the actual contract is "production callers always pass a relation kind; the single-valued fallback is the documented test-double surface". Same citation-hygiene severity as `rev-list_field.py::Low #1` (stale spec citation in a docstring claim) and `rev-scalars.py::Low #1` (stale TODO anchor) — the rule the docstring is trying to enforce is correct ("`_make_relation_resolver` always passes `kind=`"), but the framing leaks into the test-friendly path.

Recommended change: replace "the absence of `kind` in a new caller is a programming error, since production `_make_relation_resolver` always supplies the relation kind" with "production `_make_relation_resolver` always supplies the relation kind; the `kind=None` fallback is reserved for test-double direct callers that exercise the single-valued cache check (see `tests/types/test_resolvers.py::test_check_n1_*`)". Same calibration as the `scalars.py` "wire-level symmetric / Python-level asymmetric" framing carry-forward — error-message / docstring precision matters most for the test-double path because that path is the consumer-facing example.

```django_strawberry_framework/types/resolvers.py:127-136
    """B3: warn or raise if the relation is not planned and would lazy-load.

    ``kind`` is required (keyword-only) and accepts the ``relation_kind``
    of the field being resolved. ``"many"`` and ``"reverse_many_to_one"``
    use the many-side cache check; every other known relation shape uses
    the single-valued cache check. Pass ``kind=None`` only when you
    explicitly want the legacy single-valued check — the absence of
    ``kind`` in a new caller is a programming error, since production
    ``_make_relation_resolver`` always supplies the relation kind.
    """
```

### `_make_relation_resolver` `parent_type: type | None = None` default is a test-double surface, not a documented production fallback

`types/resolvers.py:216` and `types/resolvers.py:170` (`_field_meta_for_resolver`) both accept `parent_type: type | None = None` and the docstrings name it ("The `None` default exists for test-double direct calls; production calls always supply `parent_type=cls`."). When `parent_type=None`, `resolver_key(None, field_name, ...)` (`optimizer/plans.py:164-165`) returns the bare `field_name@path` form — distinct from the production `<TypeName>.<field>@<path>` form that the walker plans against. A test-double direct call without `parent_type` therefore guarantees the `key in planned` check at `_check_n1` (`types/resolvers.py:142`) misses for every key the walker emitted, and the test-double path falls through to the lazy-load gate.

This is shipped contract behavior (the test suite at `tests/types/test_resolvers.py:48-86` and `:446-481` exercises it intentionally), and the docstrings correctly name the test-double-only nature. Worth a small framing tightening because the production-fallback misuse path is silent: a consumer (or a future package author) who reads "production calls always supply `parent_type=cls`" but inadvertently drops the kwarg in a new call site would get every strictness check silently passing — the bare-key form would never appear in `planned` (which is always populated with the `<TypeName>.` prefix). Same `silent dead code` calibration that `rev-types__base.md` recorded for the `__init_subclass__` validation gap.

Recommended change: add a one-line `Raises` / contract note to both docstrings: "Production callers MUST pass `parent_type=cls` so the branch-sensitive resolver key matches what the optimizer walker emitted; the `None` default ONLY supports test-double direct callers exercising the single-valued / many-side code paths without a registered `DjangoType`." Doc-pass territory; no code change.

```django_strawberry_framework/types/resolvers.py:170-175
def _field_meta_for_resolver(field: Any, parent_type: type | None) -> FieldMeta:
    """Return registered ``FieldMeta`` for ``field`` when the parent type exposes it.

    The ``None`` default exists for test-double direct calls; production calls always
    supply ``parent_type=cls``.
    """
```

### `_resolver_logger` indirection via `..optimizer import logger` reads as a circular guard but is structural sibling import

`types/resolvers.py:32-34` imports the optimizer subpackage's logger with the comment "Share the optimizer subpackage's logger so consumers configuring `django_strawberry_framework` see N+1 warnings." The aliasing to `_resolver_logger` is fine, but the sibling-import shape (`from ..optimizer import logger as _resolver_logger`) reads at first glance like a circular-import workaround — the actual rationale is "the optimizer subpackage's logger is the canonical N+1-warning home; the resolvers module is the surfacing site". Today's comment names the consumer-config rationale but not the canonical-home rationale.

Severity Low because the indirection is correct and the comment captures the most important property (consumers configure `django_strawberry_framework` and pick up N+1 warnings from both subsystems through the same handler). Same comment-hygiene severity as `rev-optimizer___context.md::Low #3` (the catch-and-chain at `_context.py:126` lacks the inline comment that the catch-and-return at `_context.py:131-140` has — same "twin pattern, only one half documented" calibration).

Recommended change: extend the existing two-line comment to one extra sentence: "Share the optimizer subpackage's logger so consumers configuring `django_strawberry_framework` see N+1 warnings. The optimizer subpackage owns the canonical N+1-warning logger; this module re-exports it under a `_resolver_logger` alias so the surfacing site reads explicitly as `_resolver_logger.warning(...)` rather than as `logger.warning(...)` (which would mask the cross-subpackage origin)."

```django_strawberry_framework/types/resolvers.py:32-34
# Share the optimizer subpackage's logger so consumers configuring
# "django_strawberry_framework" see N+1 warnings.
from ..optimizer import logger as _resolver_logger
```

### GLOSSARY missing `OptimizerError` — forwarded to project pass

`OptimizerError` is the typed raise this module emits at `types/resolvers.py:152` AND the cross-subsystem typed marker recorded in `rev-exceptions.md::Low #2` ("only `ConfigurationError` has a GLOSSARY entry; forwarded base/sibling glossary coverage to project pass"). The Medium above's verbatim GLOSSARY replacement prose for `Strictness mode` cites `[OptimizerError](#optimizererror)` — that anchor will resolve correctly only once `rev-exceptions.md`'s forward lands at the project pass. NOT re-filed as a per-file GLOSSARY edit here; recap only so Worker 2 / Worker 3 see the in-cycle interaction between this Medium and the deferred project-pass authoring.

### `_check_n1` does not log `kind` in the strictness-warn message even though the kind is the load-bearing dispatch axis

The warn branch at `types/resolvers.py:154` emits `_resolver_logger.warning("Potential N+1 on %s", field_name)` with `field_name` only. Strictness-warn is the consumer-visible diagnostic path; the field name alone is not enough to disambiguate which cardinality branch the optimizer was supposed to plan (many-side vs single-side has different fixes — `Meta.optimizer_hints` for the many side typically points at a `prefetch_related` target, the single side at a `select_related` chain). Today's tests pin the message verbatim (`tests/types/test_resolvers.py:321`'s `assert any("Potential N+1 on category" in r.message for r in caplog.records)`), so widening to `"Potential N+1 on %s (kind=%s)"` is a test-touching change.

Severity Low because the diagnostic is functional — a consumer reading the warning knows which field needs planning — and the kind information is reachable through `Meta.optimizer_hints` introspection. Same calibration as the `rev-optimizer__hints.md::OptimizerHint.prefetch_obj repr=False` Low recorded in worker memory — small consumer-debug-surface miss where the load-bearing dispatch information is one introspection call away.

Recommended change defer-with-trigger: defer until the second consumer feedback report names "couldn't tell which side of the cardinality to fix from the warning"; then widen the message format and update the test pin.

```django_strawberry_framework/types/resolvers.py:153-154
    if strictness == "warn":
        _resolver_logger.warning("Potential N+1 on %s", field_name)
```

## What looks solid

### DRY recap

- **Existing patterns reused.** `resolver_key` / `runtime_path_from_info` from `optimizer/plans.py` (`types/resolvers.py:44`) carry the branch-sensitive resolver-key contract for both the FK-id elision and N+1 dispatches; `is_many_side_relation_kind` / `relation_kind` from `utils/relations.py` (`types/resolvers.py:46`) carry the single classifier the package's converters, resolvers, and optimizer all read against; `FieldMeta.is_many_side` / `FieldMeta.relation_kind` properties (`optimizer/field_meta.py:107-115`) are read at `types/resolvers.py:244` / `:246` instead of re-deriving cardinality from raw flags; `_get_context_value` from `optimizer/_context.py` (`types/resolvers.py:40-42`) at three call sites (`:61-65`, `:138`, `:150`) for the dict-vs-attribute context-read symmetry; `OptimizerError` from `..exceptions` is the typed raise for the strictness contract (`:30`, `:152`); `_resolver_logger` alias shares the optimizer subpackage's logger so consumer logging config picks up both subsystems' N+1 warnings (`:34`).
- **New helpers considered.** `_resolver_key_from_info(parent_type, field_name, info)` evaluated at two call sites (`_is_fk_id_elided` and `_check_n1` build the same key from the same triple) but rejected as defer-with-trigger because both bodies put `key in elisions` / `key in planned` directly one line below the build — the helper would obscure the near-symmetric local read. `_lazy_load_check(root, field_name, *, kind)` evaluated as a single dispatcher unifying `_will_lazy_load_single` / `_will_lazy_load_many` but rejected because the two checks have load-bearing different invariants per docstring (`:97-101` and `:104-116`) — collapsing them through `if is_many_side_relation_kind(kind): ... else: ...` would force a runtime branch on every call and obscure the "many-side intentionally does NOT use the `__dict__` short-circuit" property the test at `tests/types/test_resolvers.py:391-415` pins explicitly. `_name_resolver` (`:157-167`) at three call sites is the right granularity for the rename — already extracted.
- **Duplication risk in the current file.** Three near-twin closure bodies inside `_make_relation_resolver` (`many_resolver` / `reverse_one_to_one_resolver` / `forward_resolver` at `:248-272`) all share the `_check_n1(info, root, field_name, parent_type, kind=kind)` prelude. Intentionally three separate closures because (a) the closure structure is what makes Strawberry's `getattr(self, name)` resolution find a Python-function callable with a writeable `__name__`; (b) the three cardinality branches each have a different post-prelude body (`list(getattr(root, name).all())` / `try/except DoesNotExist` / `getattr(root, name)` with FK-id elision short-circuit), and folding through a single dispatcher with `if kind == ...` would obscure the cardinality-specific shape that the test suite at `tests/types/test_resolvers.py:48-86` pins per-branch. Same calibration as `rev-filters__sets.md`'s `apply_sync` / `apply_async` "load-bearing distinction, don't fold through a shared dispatcher" carry-forward.

### Other positives

- Test discipline: `tests/types/test_resolvers.py` covers every cardinality branch (many-side, reverse OneToOne, forward FK), the FK-id elision happy path (`test_b2_forward_fk_id_elision_returns_stub_without_accessing_relation` at `:89`), null-FK short-circuit (`test_b2_forward_fk_id_elision_returns_none_for_null_fk` at `:180`), parent-type isolation under shared field names (`test_b2_forward_fk_id_elision_does_not_leak_across_parent_types` at `:219`), bare-field-name resolver-key rejection (`test_b2_forward_fk_id_elision_ignores_bare_field_name_key` at `:245` and `test_check_n1_ignores_bare_field_name_key` at `:267`), the `__dict__` short-circuit asymmetry between single-valued and many-side cache checks (`test_check_n1_many_side_kind_treats_consumer_set_attribute_as_lazy` at `:391` — parametrized over `"many"` and `"reverse_many_to_one"`), the strictness `off` / `warn` / `raise` triplet, and the spec-019 Slice 1 (rev4) router/connection-aware additions (`test_fk_id_elision_stub_sets_state_db_via_router_db_for_read` at `:572` through `:728`).
- Error-handling shape: the strictness-raise path emits `OptimizerError`, the typed marker the package's optimizer subsystem owns, and is `import`-paired with `..exceptions` at the top of the module (`:30`). The strictness-warn path uses the optimizer subpackage's logger so consumer logging config flows through. The reverse OneToOne branch isolates the `DoesNotExist` exception class to the related-model attribute (`field_meta.related_model.DoesNotExist`) so no module-level Django-specific catch is needed.
- Design choice: the `_EMPTY_ELISIONS: frozenset[str] = frozenset()` module-level sentinel at `:50` is the right shape for the per-call "no elisions registered" branch — `_get_context_value(..., _EMPTY_ELISIONS)` at `:61-65` avoids allocating a fresh empty set per forward-resolver dispatch, and the immutable sentinel rules out accidental mutation. Same calibration as `rev-optimizer___context.md`'s `_MISSING` sentinel.
- Design choice: the four single-purpose private helpers (`_is_fk_id_elided`, `_build_fk_id_stub`, `_will_lazy_load_single`, `_will_lazy_load_many`) are each ~10-15 lines and one responsibility — the module's larger functions (`_field_meta_for_resolver` at 44 lines / 7 branches, `_make_relation_resolver` at 57 lines / 3 branches) read clearly because the per-cardinality dispatch is the only branching that survives at the top level; the helpers absorb the per-branch detail.
- `router.db_for_read` is consulted at the right place (`_build_fk_id_stub` at `:82`) with the right `instance=` hint (parent row if available, `None` otherwise) per spec-019 Slice 1 Decision 5; the FK-id stub stamps `state.adding = False` (`:80`) so consumer-side `__init__` introspection sees the stub as a loaded row, matching the contract `tests/types/test_resolvers.py:572-660` pins.
- GLOSSARY drift quick-check: the resolver-related symbols `FK-id elision` (`docs/GLOSSARY.md:496-511`) and `Relation cardinality and resolver behavior` (`docs/GLOSSARY.md:880-926`) are aligned with this module's behavior — both name the FK-id stash on `info.context`, the many-side returns-list contract, and the consumer-`strawberry.field` override preservation. The only drift recorded is the Medium above (`Strictness mode` `RuntimeError` → `OptimizerError`). `OptimizerError` itself is absent from GLOSSARY (forwarded per `rev-exceptions.md` to project pass).
- Comment hygiene: zero TODO anchors (shadow overview: "TODO comments: none."), zero repeated string literals (shadow overview: "Repeated string literals: None."), zero stale `spec-NNN` citations against the docs/SPECS/ archive sweep. The single spec citation at `:59` (`spec-011 Decision 7 #"FK-id elision scoping"`) is symbol-qualified per `AGENTS.md` rule 27. Note: spec-011 was renamed/superseded in `rev-types__relay.md`'s 7-site sweep to spec-015; check whether this `:59` citation should follow the same rewrite at folder/project pass.

### Summary

`types/resolvers.py` is a tight 296-line module hosting the cardinality-aware relation-resolver factory and the FK-id elision + strictness-N+1 surfacing sites. Zero High; one Medium (GLOSSARY drift on `Strictness mode` — `RuntimeError` → `OptimizerError`; verbatim replacement prose preserved); five Lows, all comment/docstring or forward to existing project-pass GLOSSARY work. The cross-folder `_field_meta_for_resolver` / `FieldMeta.from_django_field` mirror is the substantive DRY observation but is already enumerated in `rev-optimizer__field_meta.md` and owned by the upcoming `rev-types.md` folder pass per dispatch — recap-only here. The two control-flow hotspots (`_field_meta_for_resolver` 44 lines / 7 branches and `_make_relation_resolver` 57 lines / 3 branches) both read clearly because the per-cardinality dispatch is the only branching at the top level. Standard three-spawn cycle. `Status: under-review`.

---

## Fix report (Worker 2)

### Files touched
- `docs/GLOSSARY.md` `## Strictness mode` — Medium #1: swapped `"raise"` bullet from `fail-fast \`RuntimeError\`` to `fail-fast \`OptimizerError\`` (one-token substring change). Plain backticks (un-linked) per artifact fallback instruction — `OptimizerError` GLOSSARY entry is not yet authored (rev-exceptions.md forward to project pass not yet landed). `See also:` line unchanged for the same reason.
- `django_strawberry_framework/types/resolvers.py::_check_n1` — Low #1: rewrote docstring final sentence per artifact verbatim recommendation. Dropped the "programming error" framing; named the production `_make_relation_resolver` contract first, then named the `kind=None` fallback as reserved for test-double direct callers and cited the `tests/types/test_resolvers.py::test_check_n1_*` family.
- `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` — Low #2 (first site): replaced the two-line `None`-default docstring paragraph with the artifact's verbatim "Production callers MUST pass `parent_type=cls`..." contract note (test-double-only nature, branch-sensitive resolver-key matching).
- `django_strawberry_framework/types/resolvers.py::_make_relation_resolver` — Low #2 (second site): same verbatim replacement applied for parity with `_field_meta_for_resolver`. Both docstrings now state the same contract in the same words.
- `django_strawberry_framework/types/resolvers.py` `_resolver_logger` import block — Low #3: extended the two-line comment with the artifact's verbatim one-sentence canonical-home rationale ("The optimizer subpackage owns the canonical N+1-warning logger; this module re-exports it under a `_resolver_logger` alias so the surfacing site reads explicitly as `_resolver_logger.warning(...)` rather than as `logger.warning(...)` (which would mask the cross-subpackage origin)."). Forward consumer-config rationale preserved as-is.

### Tests added or updated
- None. M1 is a GLOSSARY-only one-token correction with no consumer-facing behavior change (the existing raise has been `OptimizerError` since 0.0.3 per `tests/types/test_resolvers.py::test_check_n1_*` pinning `OptimizerError` already; this cycle catches the GLOSSARY prose up to the shipped raise type). Lows #1-3 are docstring/comment-only polish — no behavior change, no test surface needed. Lows #4 (forwarded `OptimizerError` GLOSSARY entry) and #5 (deferred-with-trigger widen-warn-message-with-kind) explicitly carry no in-cycle edit per artifact prose.

### Validation run
- `uv run ruff format .` — pass / 213 files unchanged (warning emitted re COM812 ↔ formatter, pre-existing in repo, out of scope).
- `uv run ruff check --fix .` — pass / All checks passed.
- No focused test run (Worker 2 must not run pytest per `worker-2.md` hard rules).

### Notes for Worker 3
- Shadow file: not consulted. M1 + Lows #1-3 are all artifact-pre-derived verbatim edits with no AST/control-flow inspection required; the diff is the entire fix surface.
- M1 link target: the verbatim replacement prose in the artifact (`docs/review/rev-types__resolvers.md:35`) cites `[`OptimizerError`](#optimizererror)` with an in-page anchor link. The artifact's own fallback instruction (`:43-44`) authorizes plain `` `OptimizerError` `` (un-linked backticks) when the `OptimizerError` GLOSSARY entry is not present, and `grep -n "^## .*OptimizerError" docs/GLOSSARY.md` returns zero matches as of this cycle — `rev-exceptions.md`'s forwarded `OptimizerError` GLOSSARY entry has not yet landed at the project pass. Edit therefore used un-linked backticks per fallback. When the project pass authors the `OptimizerError` entry, the `Strictness mode` `"raise"` bullet can be promoted to `[`OptimizerError`](#optimizererror)` in a sweep with the `**See also:**` line tail.
- Low #2 docstring symmetry: artifact named both `_field_meta_for_resolver` (`:170-175`) and `_make_relation_resolver` (`:216`) as the two sites needing the same tightening; both now carry the same five-line "Production callers MUST pass `parent_type=cls`..." contract note. The earlier two-line "test-double direct calls" phrasing is fully replaced (no overlap preserved) — the new wording is strictly more informative.
- Low #3 (`_resolver_logger`): extended the existing two-line comment by appending a third logical statement (canonical-home rationale) as a follow-on sentence. The artifact recommends a single extended comment block, not a split — kept as one contiguous comment per artifact prose.
- Low #4 forwarded: `OptimizerError` GLOSSARY entry not authored this cycle per artifact prose ("NOT re-filed as a per-file GLOSSARY edit here; recap only"). Owned by `rev-exceptions.md`'s forwarded project-pass GLOSSARY authoring.
- Low #5 deferred-with-trigger: `_check_n1` warn-branch message format unchanged (`"Potential N+1 on %s"` with `field_name` only); test pin at `tests/types/test_resolvers.py:321` `"Potential N+1 on category"` remains untouched. Trigger captured in artifact prose: second consumer feedback report naming "couldn't tell which side of the cardinality to fix from the warning"; then widen to `"Potential N+1 on %s (kind=%s)"` and update the pinning test.
- `uv.lock` not touched (clean against HEAD); no `uv run ...` dependency-change call surface this cycle.
- Concurrent maintainer activity flagged by `git status` (KANBAN, finalizer.py, relations.py, relay.py, base.py, builder docs, kanban app, etc.) is untouched per AGENTS.md #33.

---

## Comment/docstring pass

Folded into this consolidated single-spawn (shape #4) per dispatch — Lows #1-3 ARE the comment/docstring pass; no separate Worker 3 logic-acceptance gate is required because the Medium is a one-token GLOSSARY swap with no consumer-facing behavior change and the in-cycle Lows are all docstring/comment-only polish that cannot interact with logic.

### Files touched
- `django_strawberry_framework/types/resolvers.py::_check_n1` — Low #1 docstring rewrite.
- `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` + `::_make_relation_resolver` — Low #2 parallel docstring rewrites.
- `django_strawberry_framework/types/resolvers.py` `_resolver_logger` import block — Low #3 comment extension.
- `docs/GLOSSARY.md` `## Strictness mode` — Medium #1 one-token swap (counted under logic pass for severity but applied in the same consolidated edit as the docstring polish).

### Per-finding dispositions
- Medium 1 (`Strictness mode` GLOSSARY drift): applied per artifact verbatim replacement, with the plain-backticks fallback for the `OptimizerError` reference per artifact `:43-44` since `rev-exceptions.md`'s forwarded GLOSSARY entry has not landed.
- Low 1 (`_check_n1` `kind=None` docstring framing): applied per artifact verbatim recommendation. "Programming error" framing removed; test-double fallback contract named first-class with `test_check_n1_*` family cited.
- Low 2 (`parent_type=None` test-double surface on `_field_meta_for_resolver` + `_make_relation_resolver`): applied per artifact verbatim recommendation at both sites; identical wording at both for parity.
- Low 3 (`_resolver_logger` indirection comment): applied per artifact verbatim recommendation as one extended comment block.
- Low 4 (GLOSSARY missing `OptimizerError`): no edit — forwarded to project pass per artifact prose. Dispatch prompt confirms this is Low #4 forwarded/deferred.
- Low 5 (`_check_n1` warn-branch missing `kind`): no edit — defer-with-trigger per artifact prose. Dispatch prompt confirms this is Low #5 deferred.

### Validation run
- `uv run ruff format .` — pass / 213 files unchanged.
- `uv run ruff check --fix .` — pass / All checks passed.

### Notes for Worker 3
- All in-cycle edits are verbatim lifts from artifact-pre-derived replacement prose; no Worker 2 invention.
- Severity calibration sibling for the GLOSSARY one-token swap: `rev-management__commands__export_schema.md::M1` (per artifact `:22`) — both are `shipped` public-contract entries lagging their actual implementation.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Per `AGENTS.md` line 21 ("Do not update `CHANGELOG.md` unless explicitly instructed"), AND the dispatch prompt's explicit calibration "Changelog `Not warranted` (GLOSSARY tightening + docstring polish) citing AGENTS.md + active plan silence." The active plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle. The Medium is a GLOSSARY one-token correction documenting the actually-shipped `OptimizerError` raise — the raise itself has been `OptimizerError` since 0.0.3 per `tests/types/test_resolvers.py::test_check_n1_*` pinning; no consumer-visible behavior changes this cycle. The Lows are docstring/comment-only polish on private helpers. Neither half qualifies for a `CHANGELOG.md` entry, and neither was authorized.

Calibration siblings for `Not warranted` on prior 0.0.7 GLOSSARY-tightening cycles: `optimizer/extension.py` consolidated (three-entry GLOSSARY lift), `optimizer/field_meta.py` three-pass (GLOSSARY widening with no exception-message substring change), `optimizer/hints.py` consolidated (`OptimizerHint` Validation paragraph lift), `types/relay.py` consolidated (M1 GLOSSARY lift + new entry, no exception substring change). All four match the same shape: GLOSSARY catches up with already-shipped behavior; no consumer-visible substring at error sites changes; CL `Not warranted` is correct.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / 213 files unchanged.
- `uv run ruff check --fix .` — pass / All checks passed.

---

## Verification (Worker 3)

### Logic verification outcome
- **M1 GLOSSARY drift on `Strictness mode`**: addressed. `docs/GLOSSARY.md:1106` now reads `fail-fast \`OptimizerError\`` (was `\`RuntimeError\``). Plain un-linked backticks per artifact `:43-44` fallback (the `OptimizerError` GLOSSARY entry is not yet authored; `rev-exceptions.md` forwards it to the project pass). Surrounding entry shape preserved char-for-char.
- **Low #1 (`_check_n1` `kind=None` docstring framing)**: addressed verbatim. "Programming error" framing dropped at `resolvers.py:131-140`; "Production `_make_relation_resolver` always supplies the relation kind; the `kind=None` fallback is reserved for test-double direct callers..." replacement landed including the `tests/types/test_resolvers.py::test_check_n1_*` citation. AGENTS rule 27 `path::QualifiedName` form respected.
- **Low #2 (`parent_type=None` test-double surface, two sites)**: addressed at both `_field_meta_for_resolver` (`resolvers.py:174-181`) and `_make_relation_resolver` (`resolvers.py:222-229`) with identical "Production callers MUST pass `parent_type=cls` so the branch-sensitive resolver key matches what the optimizer walker emitted; the `None` default ONLY supports test-double direct callers exercising the single-valued / many-side code paths without a registered `DjangoType`." prose verbatim per the artifact's recommended change.
- **Low #3 (`_resolver_logger` indirection comment)**: addressed at `resolvers.py:32-37`. Existing two-line comment extended with the canonical-home rationale verbatim ("The optimizer subpackage owns the canonical N+1-warning logger; this module re-exports it under a `_resolver_logger` alias so the surfacing site reads explicitly as `_resolver_logger.warning(...)` rather than as `logger.warning(...)` (which would mask the cross-subpackage origin).") as a contiguous comment block per artifact prose.
- **Low #4 (GLOSSARY missing `OptimizerError`)**: forwarded to project pass per artifact prose at `:110-112`. No in-cycle edit required; recap-only.
- **Low #5 (`_check_n1` warn message missing `kind`)**: deferred-with-trigger per artifact prose at `:120`. No in-cycle edit; trigger ("second consumer feedback report naming 'couldn't tell which side of the cardinality to fix from the warning'") captured verbatim in artifact for future-cycle revival.

### DRY findings disposition
- Cross-folder `_field_meta_for_resolver` ↔ `FieldMeta.from_django_field` mirror: recap-only per dispatch; owned by the upcoming `rev-types.md` folder pass and already enumerated in `rev-optimizer__field_meta.md::## DRY analysis #1`. No in-cycle act-now extraction expected at this per-file scope.
- `_resolver_key_from_info(...)` helper: defer-with-trigger per artifact's "any third site in this file that needs the same key-from-info build" gate. Current two call sites (`_is_fk_id_elided`, `_check_n1`) both place `key in elisions` / `key in planned` directly one line below the build — collapsing through a helper would obscure the near-symmetric local read. Trigger captured verbatim.

### Temp test verification
- No temp test files created. Cycle scope is M1 GLOSSARY one-token correction + four docstring/comment-only Lows; no behavior surface to probe. M1 substring change is documentation catching up with already-shipped raise behavior (`OptimizerError` pinned by existing `tests/types/test_resolvers.py::test_check_n1_*` regression coverage per artifact `:137`).

### Changelog disposition verification
- `git diff -- CHANGELOG.md` is empty (verified). ✓
- Disposition cites BOTH (a) `AGENTS.md` line 21 ("Do not update `CHANGELOG.md` unless explicitly instructed") AND (b) active plan `docs/review/review-0_0_7.md` silence on changelog authorization for this cycle. ✓
- "Internal-only" framing honest: M1 is a GLOSSARY one-token correction documenting the actually-shipped `OptimizerError` raise (no consumer-visible substring change at the error site itself, since the raise has been `OptimizerError` since 0.0.3); Lows #1-3 are docstring/comment polish on private helpers (`_check_n1`, `_field_meta_for_resolver`, `_make_relation_resolver`, `_resolver_logger` are all leading-underscore-private, not in `types/__init__.py::__all__`). The four-cycle calibration siblings named in the disposition (`optimizer/extension.py`, `optimizer/field_meta.py`, `optimizer/hints.py`, `types/relay.py`) match this shape verbatim.

### Ruff spot-verify
- `uv run ruff format --check django_strawberry_framework/types/resolvers.py` — `1 file already formatted` (pass).
- `uv run ruff check django_strawberry_framework/types/resolvers.py` — `All checks passed!` (pass).

### Concurrent maintainer hunks
- `docs/GLOSSARY.md` carries TWO concurrent hunks past M1: a new `SyncMisuseError` top-level entry at `:1114-1124` plus a `Relay Node integration` Shipped-behavior bullet at `:937+1`. Both attribute to the prior `rev-types__relay.md` sibling cycle (`Status: verified`, `[x]`-marked at `docs/review/review-0_0_7.md` per worker-3 memory entry under `## types/relay.py`). Same dirty-tree-from-verified-sibling attribution pattern recorded in prior folder-pass cycles. The current cycle's GLOSSARY scope is strictly `:1106` `Strictness mode` one-token swap.
- `git status` working tree concurrent activity (KANBAN, finalizer.py wider hunks, base.py, builder docs, kanban app) flagged by Worker 2 under AGENTS.md #33 — untouched and non-overlapping with this cycle's diff.

### Verification outcome
`cycle accepted; verified` — top-level `Status: verified` set; checklist box at `docs/review/review-0_0_7.md:90` to be marked `[x]`.
