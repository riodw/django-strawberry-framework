# Folder review: `django_strawberry_framework/types/`

Status: verified

## DRY analysis

- **Existing patterns reused (folder scope).** Every cross-file collaboration inside `types/` already routes through a single documented helper, and no sibling re-implements another sibling's contract:
  - `DjangoTypeDefinition` (`types/definition.py:15-44`) is the single canonical metadata record. It has exactly one construction site (`types/base.py:222-240` inside `DjangoType.__init_subclass__`) and every reader inside the folder routes through `registry.get_definition`: `finalizer.py:115,150` (Phase 1 + Phase 2 consumers), `relay.py:78,134,297` (model lookup + composite-pk gate + initial queryset), `resolvers.py:165-167` (field_meta resolution + N+1 check). No sibling rebuilds the metadata record; no sibling reaches for `cls.__django_strawberry_definition__` outside `relay.py`'s documented Phase 2.5 reads.
  - The `field_map: dict[str, FieldMeta]` shape is the inter-module contract — built once at `base.py:168` (`{snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}`) and read at four sites without rebuild: `finalizer.py:192` (resolved-relation field_meta thread-through, the M2 fix from `rev-types__finalizer.md`), `resolvers.py:167` (the canonical FieldMeta fast-path in `_field_meta_for_resolver`), `relay.py` (indirectly through `DjangoTypeDefinition.model` reads), and the optimizer subpackage (`walker.py:114`, `extension.py:677-678`) — all consume the same shape contract.
  - The `PendingRelation` + `PendingRelationAnnotation` scaffolding (`types/relations.py:13-47`) is a pure leaf module: produced once at `base.py:801-818` (the inlined-from-helper site after the `rev-types__base.md` L2 fix) and consumed once at `finalizer.py:114-138` (the `iter_pending_relations` drain + annotation rewrite). The sentinel + metaclass `__repr__` is the only `__annotations__`-leaking sentinel in the package and is the canonical "sentinel discipline + repr-shaping" example documented in `worker-memory/worker-1.md`.
  - The three sibling error formatters now form a complete documented family: `_format_unknown_fields_error` (`base.py:394-402`), `_format_unresolved_targets_error` (`finalizer.py:21-29`), `_format_ambiguity_error` (`finalizer.py:48-55`). Each docstring cross-references the others (per the converters-cycle carry-forward); no fourth formatter has landed in `converters.py`, `relations.py`, `relay.py`, or `resolvers.py` without joining the family — confirmed by grep.
  - Cardinality classification routes through `FieldMeta.from_django_field` (`optimizer/field_meta.py:113-170`) and `is_many_side_relation_kind` / `relation_kind` (`utils/relations.py:39-70`). Inside `types/` the canonical builder is consumed at `base.py:168` (`field_map` construction), `converters.py:319` (the `resolved_relation_annotation` fallback path), and `resolvers.py:170-183` (the test-double fallback that was DRY-aligned with the canonical nullable rule and target-column reads in the `rev-types__resolvers.md` M1 fix). No sibling re-implements the cardinality dispatch.
  - Relay lifecycle helpers (`apply_interfaces`, `implements_relay_node`, `_check_composite_pk_for_relay_node`, `install_relay_node_resolvers`) live in `relay.py` and are consumed exclusively from `finalizer.py:148-159` Phase 2.5. The three-axis discriminator pattern (`cls.__dict__` membership at `install_is_type_of`, `relay.Node in interfaces` at `_build_annotations`, `__func__` identity at `install_relay_node_resolvers`) is documented per-function in `relay.py` and is the canonical "structurally-distinct discriminators at distinct lifecycle phases" pattern called out in worker-memory.
  - The two `Meta` whitelists (`ALLOWED_META_KEYS` at `base.py:60-69`, `DEFERRED_META_KEYS` at `base.py:48-56`) are the single-source-of-truth Meta-key contract. The 5 deferred slots are validated-but-ignored on the Meta side and were removed from `DjangoTypeDefinition` slots in the `rev-types__definition.md` M1 cycle (the parallel surface gap is closed).
- **New helpers a fix might justify (folder scope).** Four extractions are deferred across the per-file artifacts; folder-scope bundling is the right shape:
  - `_collect_consumer_authored_fields(cls, fields) -> tuple[frozenset[str], dict[str, frozenset[str]]]` and `_assert_no_relay_id_collision(cls, relay_shaped)` from `rev-types__base.md` M3.
  - `_apply_id_filter_and_materialize_single` / `_apply_id_filter_and_materialize_many` from `rev-types__relay.md` M1.
  - `_model_for(type_cls) -> type[models.Model]` from `rev-types__relay.md` L5 (collapses `cls.__django_strawberry_definition__.model` reads at `relay.py:78,134,297`).
  Evaluated together at the folder pass; see Medium §M2 below for the bundling rationale and trigger conditions.
- **Duplication risk across the folder.** The shadow overviews' Repeated-string-literals sections show **no literal appears in two or more sibling overviews**. Every repeated literal listed is intra-file and already documented in its per-file artifact:
  - `base.py`: `optimizer_hints` (4x — Meta-key reads in `_meta_optimizer_hints`, `_validate_meta`, `_validate_optimizer_hints`, `DjangoTypeDefinition` construction), `description` (2x — `getattr(meta, "description", ...)` + `DjangoTypeDefinition(description=...)`), `interfaces` (2x — `_validate_interfaces` reads). All intra-file Meta-key surface, already carried by the `_ValidatedMeta` thread-through that landed in the base.py cycle.
  - `relay.py`: `__func__` (2x — the identity discriminator pair at `relay.py:477-478` inside `install_relay_node_resolvers`, load-bearing).
  - Every other sibling: zero repeated literals.
  The cross-file scan is clean: no folder-scope literal DRY consolidation is needed. The only across-file string-shape concern was the dead `convert_relation` mention surviving in the subpackage docstring after the converters cycle removed the symbol — flagged Medium §M1 below.

## High:

None.

## Medium:

### M1 — `types/__init__.py` subpackage docstring still names `convert_relation` after the symbol was removed

`types/__init__.py:6` reads: "Internal helpers (``convert_scalar``, ``convert_relation``, ``convert_choices_to_enum``, ``_make_relation_resolver``, ``_attach_relation_resolvers``) stay reachable via their dotted submodule paths but are not exposed here." The `convert_relation` mention is now stale — the symbol was deleted from `types/converters.py` in the `rev-types__converters.md` M1 cycle (verified: `grep -n "^def convert_relation" django_strawberry_framework/types/converters.py` returns zero matches; the symbol is no longer importable). The subpackage docstring is the "what lives here" surface a consumer reads when scanning the `types/` package boundary; advertising a no-longer-importable helper there is the same docstring-vs-reality drift pattern recorded in worker-memory ("a name in a public-facing docstring after the symbol was removed is consumer-facing surface drift"). The converters cycle's "Out-of-scope stale references" carry-forward at `rev-types__converters.md:251,279` explicitly tagged this for the folder pass.

Recommended change: remove `convert_relation` from the parenthesized list, leaving the four remaining helpers (`convert_scalar`, `convert_choices_to_enum`, `_make_relation_resolver`, `_attach_relation_resolvers`). The docstring's general framing (internal helpers reachable via dotted submodule paths) is correct and should be preserved; only the stale name needs to go.

Two adjacent stale-mention sites outside the folder boundary are noted for the project pass (out of scope here): `registry.py:6` (module docstring "Used by: types.converters.convert_relation for relation resolution") and `tests/optimizer/test_extension.py:1859,1960` (fixture comment text). The folder-pass fix touches only `types/__init__.py`; the others are project-pass / cross-folder cleanup.

Test expectation: none. The fix is a docstring edit; no test pins the prior wording (`grep` for "``convert_relation``" across `tests/` returns zero matches).

```django_strawberry_framework/types/__init__.py:1-14
"""Type-system subsystem: ``DjangoType``, converters, and relation resolvers.

This subpackage re-exports the consumer-facing ``DjangoType`` class so
``from django_strawberry_framework.types import DjangoType`` works the same
way the previous flat ``types.py`` module did. Internal helpers
(``convert_scalar``, ``convert_relation``, ``convert_choices_to_enum``,
``_make_relation_resolver``, ``_attach_relation_resolvers``) stay reachable
via their dotted submodule paths but are not exposed here.

Dependency direction: this subpackage consumes ``django_strawberry_framework
.optimizer`` (FieldMeta, OptimizerHint, plan helpers, framework-wide
logger).  The optimizer subpackage must not import back from ``types/``;
shared primitives belong in ``optimizer/`` or in a sibling utility module.
"""
```

### M2 — bundle four deferred extractions into one follow-up cycle on the `__init_subclass__` → `field_map` → resolver pipeline

Four deferred extractions accumulated across the per-file artifacts touch the same `__init_subclass__` → `DjangoTypeDefinition.field_map` → resolver-attach pipeline and naturally compose:

1. **`_collect_consumer_authored_fields(cls, fields)`** and **`_assert_no_relay_id_collision(cls, relay_shaped)`** from `rev-types__base.md` M3 — extract the two largest blocks of `DjangoType.__init_subclass__` (the four-corner consumer-override collection at `base.py:170-187` and the Relay-id collision guard at `base.py:189-213`). These would drop `__init_subclass__`'s line count from ~98 to ~60 and remove the top-level method's reach into class-level annotation introspection.
2. **`_apply_id_filter_and_materialize_single` / `_apply_id_filter_and_materialize_many`** from `rev-types__relay.md` M1 — collapse the structural duplication between the sync/async sibling pairs (`_resolve_node_default` + `_resolve_node_async`; `_resolve_nodes_default` + `_resolve_nodes_async`). The four resolvers must stay in lockstep across future spec changes; today the lockstep is enforced only by the test suite.
3. **`_model_for(type_cls) -> type[models.Model]`** from `rev-types__relay.md` L5 — collapse the three remaining `cls.__django_strawberry_definition__.model` reads at `relay.py:78,134,297` into one helper aligned with the existing `_initial_queryset` centralization (`relay.py:264-271`).

Per-file artifacts deferred each individually with the rationale "compose with the next refactor". Folder-pass calibration: bundling these as one cycle (sequenced base → relay so the base extractions land first and free up the `__init_subclass__` surface) is the right shape — each individual extraction is a 10-30 line refactor with no behavior change, but together they reshape the `types/` folder's two largest control-flow surfaces (`base.__init_subclass__` and the four `relay._resolve_*` pairs). Trigger condition: the next review cycle on `types/base.py` (which `rev-types__base.md` Fix-report deferrals already flagged) OR the next behavior change to any of the four Relay resolvers — whichever comes first. Until then, the deferrals stand and no in-cycle action is needed.

Recording at folder pass so the deferrals don't fragment further. The cross-cutting field-meta-thread-through pattern that landed in the `rev-types__finalizer.md` M2 fix (and the `rev-types__resolvers.md` M1 alignment) is the template — the same "use the pre-computed value from `field_map` rather than rebuild" discipline applied to the resolver-attach pipeline.

## Low:

### L1 — `types/__init__.py` does not document the cross-folder import direction it depends on

The subpackage docstring at `types/__init__.py:10-13` correctly states the one-way dependency direction: "this subpackage consumes ``django_strawberry_framework.optimizer`` (FieldMeta, OptimizerHint, plan helpers, framework-wide logger). The optimizer subpackage must not import back from ``types/``; shared primitives belong in ``optimizer/`` or in a sibling utility module." The contract is accurate (`grep -rn "from ..types\|from django_strawberry_framework.types" django_strawberry_framework/optimizer/` returns zero matches). What's missing is the inverse direction from `types/` into `utils/`: every sibling that needs `snake_case`, `pascal_case`, `RelationKind`, or `relation_kind` reaches into `..utils` (six call sites: `base.py:42`, `converters.py:47`, `finalizer.py:46`, `relations.py:24`, `resolvers.py:46`). The docstring's "consumes optimizer" framing is correct but reads as exclusive — a future maintainer might infer `utils/` is off-limits.

Recommended change in a future comment pass: extend the dependency-direction paragraph one sentence — "this subpackage also consumes leaf helpers from ``..utils`` (`snake_case`, `pascal_case`, `RelationKind`, `relation_kind`); the inverse direction is forbidden by the same rule." Doc-only.

### L2 — `__init__.py` re-export contract is two symbols; matches `AGENTS.md` exactly but is silent on `finalize_django_types`'s consumer surface

`types/__init__.py:19` declares `__all__ = ("DjangoType", "finalize_django_types")`. The two re-exports match `AGENTS.md:8` ("``__init__.py`` re-exports DjangoType and DjangoOptimizerExtension") for the type-side surface. Both symbols are also re-exported from the top-level package: `django_strawberry_framework/__init__.py:1-23` exposes `DjangoType` and `finalize_django_types` at the package root. The folder `__init__.py` is therefore a redundant convenience surface for `from django_strawberry_framework.types import DjangoType` (the dotted path), while the top-level export is the canonical `from django_strawberry_framework import DjangoType` (the short path).

Both shapes work today and tests use both forms; the redundancy is not a bug. The Low is documentation-only: the subpackage docstring doesn't say "this folder re-exports the same two symbols the top-level package exposes; consumers can use either path." A future maintainer might wonder which is canonical. Comment-pass polish; defer.

### L3 — `types/__init__.py` import order does not match the documented dependency direction

`types/__init__.py:16-17` imports `from .base import DjangoType` first, then `from .finalizer import finalize_django_types`. The dependency direction inside the folder is `base.py` (consumer of `converters`, `definition`, `relations`, `relay`) and `finalizer.py` (consumer of `converters`, `relations`, `relay`, `resolvers`) — they sit at the same layer of the DAG, but `base.py` is the collection-phase entry point and `finalizer.py` is the finalize-phase entry point. The current order matches the lifecycle (collect before finalize). Pure ordering nit; behavior identical.

Recommended change: none required. Listed only to confirm at folder pass that the lifecycle-ordered import is intentional and should not be re-alphabetized in a future ruff/isort sweep. Pin the rationale in the comment pass if it ever becomes contentious.

### L4 — `tests/optimizer/test_extension.py` carries two stale `convert_relation` comment references; out of scope here but project-pass anchor

`tests/optimizer/test_extension.py:1859,1960` carry fixture-comment text referencing `convert_relation`. These are inside the optimizer test suite, not the `types/` folder, so they are out of scope at this folder pass. Flagging here so the project pass picks them up alongside the `registry.py:6` and `AGENTS.md:8` references the converters cycle also flagged. None affect production behavior; all are docstring/comment text that misnames a helper that was removed.

### L5 — `types/__init__.py` module docstring framing reads as Python 2 lineage ("the previous flat ``types.py`` module")

`types/__init__.py:4-5` includes the historical framing "``from django_strawberry_framework.types import DjangoType`` works the same way the previous flat ``types.py`` module did." The "previous flat types.py" was the pre-spec-014 layout; the spec-014 split turned `types.py` into the `types/` subpackage with 7 sibling modules. The framing is accurate but anchors on a historical state no consumer reading the current package would recognize. It also reads as a backward-compatibility promise (`from django_strawberry_framework.types import DjangoType` will keep working) — which IS still true and IS the intent of the re-export — but the framing depends on knowledge of the old layout to be useful.

Recommended change in a future comment pass: replace "works the same way the previous flat ``types.py`` module did" with "is the canonical import path for the consumer-facing ``DjangoType``; the folder layout (seven sibling modules) is an internal implementation detail." Doc-only; preserves the same backward-compat intent without the historical anchor.

## What looks solid

- **No cross-file literal duplication.** Per the eight shadow overviews under `docs/shadow/django_strawberry_framework__types*.overview.md`, every repeated string literal is intra-file and already documented in its per-file artifact (`base.py`: `optimizer_hints` / `description` / `interfaces`; `relay.py`: `__func__`). Cross-file dedupe is clean — no folder-level DRY consolidation is needed.
- **One-way dependency direction inside the folder.** The dependency graph is a strict DAG: `definition.py`, `relations.py`, `relay.py`, `converters.py`, `resolvers.py` are leaves with respect to the rest of the folder (each imports only from `..optimizer`, `..registry`, `..utils`, `..exceptions`, `..scalars` — never from sibling files except `relations.py` imports `..utils.relations.RelationKind` and `converters.py` imports `.relations.PendingRelationAnnotation`). `base.py` depends on `.converters`, `.definition`, `.relations`, `.relay`; `finalizer.py` depends on `.converters`, `.relations`, `.relay`, `.resolvers`. `__init__.py` depends on `.base` and `.finalizer`. No back-edges; no circular import risk introduced by any fix this cycle.
- **`DjangoTypeDefinition.field_map` is THE inter-module contract.** Built at `base.py:168` (`{snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}`) and read at `finalizer.py:192`, `resolvers.py:167`, `walker.py:114`, `extension.py:677-678` — five readers, one canonical shape, no `getattr(definition, "field_map", {})` defensive pattern anywhere (grep-verified). The shape contract assumes non-defensive access and every reader honors it. Reference shape for the package.
- **Sibling error-formatter family is complete.** Three formatters across two files (`_format_unknown_fields_error` in `base.py:394-402`; `_format_unresolved_targets_error` + `_format_ambiguity_error` in `finalizer.py:21-55`) each cross-reference the others in docstrings. The carry-forward predicted in earlier worker-memory observations is satisfied with no fourth formatter drift in `converters.py`, `relations.py`, `relay.py`, or `resolvers.py`.
- **`PendingRelation` / `PendingRelationAnnotation` scaffolding is correctly minimal.** `relations.py` is a 48-line leaf module with three symbols and one metaclass; the sentinel discipline + repr-shaping pattern is the canonical example documented in worker-memory. The `__hash__ = object.__hash__` override that landed in the `rev-types__relations.md` M1 cycle restored identity-based hashing while preserving the synthesized value-based `__eq__`, matching the `discard_pending` identity contract end-to-end.
- **Three-axis Relay discriminator pattern stays single-sited.** `cls.__dict__` membership at `install_is_type_of:76` (declared-on-this-class semantics), `relay.Node in interfaces` tuple-membership at `_build_annotations:740-741` (collection-time semantics), `__func__` identity at `install_relay_node_resolvers:477-478` (consumer-override-wins semantics). No fourth discriminator shape has slipped in; each is test-pinned in `tests/types/test_relay_*` and matches the worker-memory "structurally-distinct discriminators at distinct lifecycle phases" calibration.
- **Optimizer→types hand-off via `_context.py` is exemplary.** `types/resolvers.py:35-43` reads the four `DST_OPTIMIZER_*` constants through `get_context_value` (single read seam) while `optimizer/extension.py:635-644` writes through `stash_on_context` (single write seam). Zero string-key drift between writer and reader; the symmetric load-bearing parallel is documented in both modules' docstrings. Held up as the reference shape for any future cross-subpackage contract.
- **`finalize_django_types` lifecycle docstring is now accurate.** After the `rev-types__finalizer.md` M3 docstring rewrite, the four phases (Phase 1 failure-atomic relation classification + primary-ambiguity audit; Phase 2 resolver attach; Phase 2.5 interface injection + Relay-node setup; Phase 3 `strawberry.type` decoration), the once-only entry-guard, and the partial-failure recovery posture (via the per-entry `definition.finalized` boolean) are all documented in one place. Matches the implementation; no docstring-vs-reality drift remains.
- **Comment surface tells one coherent story across the folder.** After the cycle's comment passes:
  - `definition.py`'s class docstring (after L3) enumerates the four load-bearing invariants (`field_map` ownership, `selected_fields` ordering, `finalized`-once semantics, four-corner override contract) that the rest of the folder reads.
  - `base.py`'s `_validate_meta`/`_validate_optimizer_hints` docstrings narrate the `_ValidatedMeta` thread-through that the M1+M2 fix introduced; `_build_annotations`'s comment block names the import-order trap spec-014 H1 closed.
  - `converters.py`'s module docstring (after L1) enumerates the actual public surface (`convert_scalar`, `convert_choices_to_enum`, `resolved_relation_annotation`, `SCALAR_MAP`) and documents `SCALAR_MAP` as a mutable extension point with last-write-wins semantics.
  - `finalizer.py`'s module + function docstrings (after L5+M3+L1) name every phase, the once-only gate, and the `mark_finalized()` lifecycle.
  - `relations.py`'s module docstring (after L4) and class docstrings (after L1+L2+L3+L5) name producer + consumer sites and the identity-match `discard_pending` contract.
  - `relay.py`'s composite-pk gate carries the Phase 2.5 ordering note (L1); `_apply_node_filter`'s color-agnostic docstring (L4); `_resolve_id_default`'s proxy-model rationale (L3).
  - `resolvers.py`'s logger-share comment (L1) and the `parent_type=None` test-double note (L3) pin the cross-module re-export surface and the test-only API surface.

### Summary

`types/` is a 7-sibling subpackage centred on a single canonical metadata record (`DjangoTypeDefinition`) with one construction site (`base.py:__init_subclass__`) and a strict DAG of intra-folder imports rooted at `base.py` and `finalizer.py`. Every cross-file collaboration routes through documented helpers; no sibling re-implements another's contract; no repeated literal appears in two or more sibling overviews. The cycle's per-file artifacts closed 11 logic findings across 7 files (3 Mediums in base.py threading `_ValidatedMeta` through `__init_subclass__`; 1 Medium each in converters.py removing dead `convert_relation`, in definition.py removing 5 future-feature slots, in finalizer.py threading `FieldMeta` from `field_map` to `resolved_relation_annotation`, in relations.py overriding `__hash__` for identity-based hashing, in resolvers.py aligning the test-double `FieldMeta` builder with the canonical one and making `_check_n1 kind` required). The folder pass surfaces 2 Mediums (M1 stale `convert_relation` mention in the subpackage docstring; M2 bundling four deferred extractions across base/relay into one follow-up cycle) and 5 Lows that are documentation polish or out-of-scope project-pass anchors. The three-axis Relay discriminator pattern, the sibling error-formatter family, and the `field_map` inter-module contract are all reference-shape patterns the folder has earned and should preserve at the project pass.

---

## Fix report (Worker 2)

Consolidated single Worker 2 pass: all in-cycle edits are module-docstring polish in `django_strawberry_framework/types/__init__.py`. M1 + L1 + L2 + L5 applied together since they all touch the same module docstring; L3 is no-change (lifecycle order is intentional). M2 and L4 are recording-only and deferred.

- **Files touched:** `django_strawberry_framework/types/__init__.py` (module docstring only).
- **Edits applied:**
  - **M1** — removed stale ``convert_relation`` from the parenthesized list of internal helpers; remaining four entries are ``convert_scalar``, ``convert_choices_to_enum``, ``_make_relation_resolver``, ``_attach_relation_resolvers``.
  - **L1** — added one sentence to the dependency-direction paragraph naming the inverse-forbidden ``..utils`` leaf-helper consumption (``snake_case``, ``pascal_case``, ``RelationKind``, ``relation_kind``).
  - **L2** — added a paragraph noting that both re-exports (``DjangoType``, ``finalize_django_types``) are also exposed at the top-level package and that the folder ``__init__.py`` is the dotted-path convenience surface.
  - **L5** — replaced the historical "works the same way the previous flat ``types.py`` module did" framing with "is the canonical import path for the consumer-facing ``DjangoType``; the folder layout (seven sibling modules) is an internal implementation detail."
- **Tests added:** none. All edits are docstring-only; the artifact explicitly notes "no test pins the prior wording" for M1, and the other items are documentation polish.
- **Validation:**
  - `uv run ruff format .` — pass (101 files unchanged).
  - `uv run ruff check --fix .` — pass (All checks passed).
  - Did not run pytest per dispatch instructions.
- **Notes for Worker 3:**
  - **M2** (bundle of four deferred extractions: `_collect_consumer_authored_fields` + `_assert_no_relay_id_collision` from `rev-types__base.md` M3; `_apply_id_filter_and_materialize_single` / `_apply_id_filter_and_materialize_many` from `rev-types__relay.md` M1; `_model_for(type_cls)` from `rev-types__relay.md` L5) is recording-only at folder pass per artifact §M2 — trigger condition is the next review cycle on `types/base.py` OR the next behavior change to any of the four Relay resolvers, whichever comes first. No in-cycle action.
  - **L3** (import-order in `types/__init__.py`) is a no-change item — the lifecycle-ordered import (`from .base` before `from .finalizer`) is intentional (collect before finalize) and should not be re-alphabetized.
  - **L4** (stale `convert_relation` references at `tests/optimizer/test_extension.py:1859,1960`) is out of scope for the folder pass and is flagged for the project pass alongside the converters-cycle deferrals at `registry.py:6` and `AGENTS.md:8`.

---

## Verification (Worker 3)

### Logic verification outcome

M1 + L1 + L2 + L5 accepted; M2 and L4 deferred (recording-only per artifact); L3 no-change (lifecycle-ordered import is intentional and preserved). `git diff -- django_strawberry_framework/types/__init__.py` shows exactly the four docstring edits the artifact's Fix report claims:

- **M1** confirmed: `convert_relation` removed from the parenthesized internal-helpers list; remaining four entries (`convert_scalar`, `convert_choices_to_enum`, `_make_relation_resolver`, `_attach_relation_resolvers`) match the artifact's recommendation. Grep-verified zero remaining `convert_relation` mentions in `types/__init__.py`.
- **L1** confirmed: new sentence "This subpackage also consumes leaf helpers from ``..utils`` (``snake_case``, ``pascal_case``, ``RelationKind``, ``relation_kind``); the inverse direction is forbidden by the same rule." appended to the dependency-direction paragraph.
- **L2** confirmed: new paragraph documents that both re-exports (`DjangoType`, `finalize_django_types`) are also exposed at the top-level package and that the folder `__init__.py` is the dotted-path convenience surface.
- **L5** confirmed: historical "works the same way the previous flat ``types.py`` module did" framing replaced with the version-neutral "is the canonical import path for the consumer-facing ``DjangoType``; the folder layout (seven sibling modules) is an internal implementation detail."

Import ordering (L3) preserved: `from .base` precedes `from .finalizer`, matching the collect-before-finalize lifecycle the artifact pins as intentional.

### DRY findings disposition

DRY analysis findings confirmed unchanged: the folder remains a strict DAG with one canonical metadata record (`DjangoTypeDefinition`), one `field_map` shape contract read by five sites, three-axis Relay discriminator pattern intact, and zero cross-file repeated literals. M2's four-extraction bundle (`_collect_consumer_authored_fields`, `_assert_no_relay_id_collision`, `_apply_id_filter_and_materialize_*`, `_model_for`) recorded for the next `types/base.py` cycle or next Relay-resolver behavior change. L4's stale `convert_relation` references at `tests/optimizer/test_extension.py:1859,1960` flagged for the project pass.

### Temp test verification

Not warranted. All edits are module-docstring polish; no behavior surface to pin. Artifact explicitly notes "no test pins the prior wording" for M1, and the other items are documentation polish.

### Verification outcome

cycle accepted; verified

---

## Comment/docstring pass

Combined with the Fix report above since the cycle is essentially all comment / docstring work in `types/__init__.py`. M1 + L1 + L2 + L5 were applied together as one docstring rewrite; L3 is no-change (lifecycle import order is intentional and should be preserved). M2 and L4 are recording-only / deferred per artifact.

---

## Changelog disposition

- **Warranted?** Not warranted.
- **Reason:** the cycle is entirely module-docstring polish in `django_strawberry_framework/types/__init__.py`. No public API change, no behavior change, no symbol add/remove (the stale `convert_relation` mention removed at M1 was already removed from `types/converters.py` in the prior `rev-types__converters.md` M1 cycle — that earlier removal carried its own warranted-deferred CHANGELOG disposition). Consistent with the worker-memory calibration "Not warranted (default for internal-only changes, docstring polish)" — no consumer-visible surface changes here.
- **What was done:** no `CHANGELOG.md` edit. Disposition recorded in this artifact per `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" plus active-plan silence.
- **Validation:** `uv run ruff format .` pass (101 files unchanged); `uv run ruff check --fix .` pass (All checks passed).

---

## Iteration log

_pending_
