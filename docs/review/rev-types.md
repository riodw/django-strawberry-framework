# Review: `django_strawberry_framework/types/`

Status: verified

Folder pass over the seven `types/` modules + `types/__init__.py`. Supersedes the
STALE on-disk artifact wholesale (was `Status: verified`; its headline act-now DRY
— extract `FieldMeta._from_field_shape` — is ALREADY merged into live source, as
`rev-types__resolvers.md` confirmed: `_field_meta_for_resolver`'s test-double
fallback now delegates to `FieldMeta._from_field_shape(field, is_relation=True)`
at `types/resolvers.py:229`). Re-raising that resolved DRY would be the #1 error
per worker memory; not re-raised. The active plan's folder-pass box at
`review-0_0_9.md` is unchecked.

All seven per-file artifacts are `Status: verified` (`rev-types__base.md`,
`rev-types__converters.md`, `rev-types__definition.md`, `rev-types__finalizer.md`,
`rev-types__relations.md`, `rev-types__relay.md`, `rev-types__resolvers.md`). The
shadow overview ran on every file including `__init__` (eight overviews under
`docs/shadow/`); Imports and Repeated-string-literal sections were compared across
all eight. This pass found two real folder-level findings, both `types/__init__.py`
module-docstring accuracy edits (the `__init__.py` is reviewed only at the folder
pass per REVIEW.md scope), so the cycle carries a real source edit →
`under-review`, not shape #5.

## DRY analysis

- **None act-now within the folder.** The relay-shaped predicate cluster
  (`_is_relay_shaped` in base.py, `implements_relay_node` in relay.py) is
  principled, not duplication (verdict below); the `relation_connections`
  producer/consumer contract is single-sourced; the `_format_*` finalizer error
  helpers and the relay encode/decode predicate pairs are deliberate
  addressability-by-design siblings already adjudicated per-file. No cross-file
  literal rises to an act-now consolidation. The stale artifact's
  `_from_field_shape` extraction is already merged (not re-raised).
- **Defer-with-trigger (carried up from the per-file artifacts, triggers
  unchanged and unfired):** (1) base.py `_is_relay_shaped` recomputed 3x per class
  creation — defer until a fourth `_validate_meta`-local `relay_shaped` consumer,
  then thread the bool through `_ValidatedMeta`; (2) relay.py
  `_resolve_node_default` / `_resolve_nodes_default` dispatch-prelude fold — defer
  until a third in-async-context resolver lands; (3) relay.py `_emits_model_label`
  / `_accepts_model_label_decode` predicate-pair collapse — defer until
  encode/decode acceptance diverges (trigger stated verbatim in the relay.py
  `:427-437` docstring); (4) finalizer.py `_format_owner_*` two-family formatter
  fold — defer until a third sidecar family lands; (5) converters.py three
  postgres-contrib defers — gate on a third soft-imported contrib field;
  (6) definition.py `_target_for_field` funnel extract — defer until a second
  cacheless consumer; (7) resolvers.py `_resolver_key_from_info` two-site collapse
  — defer until a third in-file key-from-info site.

## High:

None.

## Medium:

None.

## Low:

### L1: `types/__init__.py` docstring says "Both re-exports" but the module re-exports three symbols

`django_strawberry_framework/types/__init__.py #"Both re-exports"` (line 11) reads
"Both re-exports (``DjangoType`` and ``finalize_django_types``) are also exposed at
the top-level package". The module actually re-exports **three** symbols —
`__all__ = ("DjangoType", "SyncMisuseError", "finalize_django_types")`, with the
import block carrying `from .relay import SyncMisuseError` — and all three are also
exposed at the top-level package
(`django_strawberry_framework/__init__.py #"from .types import DjangoType, SyncMisuseError, finalize_django_types"`,
`__all__` lines 35/37/40). `SyncMisuseError` joined this surface in the 0.0.9 DRY
pass (the symbol moved to `utils/querysets.py`; `types/relay.py` re-exports it via
`from ..utils.querysets import SyncMisuseError as SyncMisuseError`), but the folder
`__init__.py` docstring's "Both"/two enumeration was never updated to "three".
Non-contract drift — the GLOSSARY is the contract surface and is current
(`#syncmisuseerror` at `docs/GLOSSARY.md:1270` and the roster line at
`docs/GLOSSARY.md:35`, shipped `0.0.5`, both accurate) — so Low, the same class as
the `types/base.py` module-docstring `Meta`-list Low a sibling cycle already
corrected. Recommended change: update line 11 to enumerate all three re-exports,
e.g. "The three re-exports (``DjangoType``, ``SyncMisuseError``, and
``finalize_django_types``) are also exposed at the top-level package", preserving
the existing convenience-surface rationale. (The first paragraph at lines 3-5 is
DjangoType-centered framing and reads fine as-is; only the "Both"/count line drifts.)

### L2: `types/__init__.py` docstring's "the optimizer subpackage must not import back from types/" is contradicted by a sanctioned lazy back-edge

`django_strawberry_framework/types/__init__.py #"The optimizer subpackage must not import back"`
(lines 16-19) states the dependency-direction rule absolutely: "this subpackage
consumes ``django_strawberry_framework.optimizer`` … The optimizer subpackage must
not import back from ``types/``." Live source carries one sanctioned exception:
`optimizer/walker.py #"from ..types.definition import origin_has_custom_id_resolver"`
(line 801) lazily imports the module-level `origin_has_custom_id_resolver` from
`types/definition.py` for the definition-less custom-`id`-resolver fallback. That
back-edge is **correct and intentional** — it is the shared spelling
`rev-types__definition.md` confirmed ("consumed both by the memoized hot path
`has_custom_id_resolver_for` and by the optimizer's definition-less fallback"), the
import is in-function with an explicit cycle-dodge comment at
`optimizer/walker.py #"Lazy import"` (lines 798-800), and it is a leaf-function
read, not module-load coupling — so it does not reintroduce the import-time cycle
the rule guards. The defect is only the docstring's absolutism: a reader auditing
the dependency graph would (correctly) find the walker back-edge and conclude
either the rule or the code is wrong. Non-contract (module docstring, not a GLOSSARY
surface), so Low. Recommended change: soften the rule to name the one sanctioned
exception, e.g. "The optimizer subpackage must not import from ``types/`` at module
load (the single permitted edge is `optimizer/walker.py`'s in-function
``origin_has_custom_id_resolver`` fallback, lazily imported to dodge the
package-init cycle); shared primitives otherwise belong in ``optimizer/`` or a
sibling utility module." The package-wide dependency-direction narrative and
whether this lazy back-edge should be canonized as the documented pattern are
forwarded to `rev-django_strawberry_framework.md` (project pass).

## What looks solid

### DRY recap

- **Existing patterns reused.** The folder's intra-package import graph is a clean
  near-DAG with documented in-function cycle-dodge pairs. `relations.py`,
  `converters.py`, and `resolvers.py` import no `types/` sibling (leaves);
  `definition.py` imports only `optimizer`/`utils` at module top and reaches
  `.relay._resolve_id_default` in-function; `relay.py` imports `.definition` at top
  and `.base` (`DEFAULT_GLOBALID_STRATEGY`, `_validate_globalid_strategy`)
  in-function; `base.py` imports `.converters`/`.definition`/`.relations`/`.relay`
  at top; `finalizer.py` is the orchestrator importing every sibling. The two
  module-top-vs-in-function pairs (`base → relay` top / `relay → base`
  in-function; `relay → definition` top / `definition → relay` in-function) are the
  documented cycle-dodge idiom. Shared vocabularies are single-sourced:
  `STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY` / `RELATION_SHAPE_VALUES`
  / `DEFAULT_RELATION_SHAPE` live once in `base.py` (relay.py and finalizer.py
  import); `MODEL_LABEL_STRATEGIES` / `TYPE_NAME_STRATEGIES` live once in `relay.py`;
  `_validate_globalid_strategy` is one validator serving both the `Meta` path and
  the `RELAY_GLOBALID_STRATEGY` setting path; `RelationKind` is imported from
  `utils/relations.py`, never re-declared.
- **New helpers considered.** No folder-level extraction warranted beyond the seven
  defer-with-trigger items carried up from the per-file passes — each gates on an
  explicit, unfired trigger and would obscure rather than clarify at the current
  site count. The stale artifact's `_from_field_shape` candidate is already merged.
- **Duplication risk across the folder.** Cross-file repeated string literals were
  compared across all eight shadow overviews: `connection` (base 3x + finalizer 3x)
  is the `Meta.connection` key name and the generated-attr suffix in two distinct
  roles, not consolidatable; `__func__` (definition 2x + relay 5x) is the MRO-unwrap
  reflective idiom applied to different descriptors per site; `FilterSet` /
  `OrderSet` (finalizer 3x; base imports the classes) are family-named error-string
  tokens pinned by tests; the strategy-string literals (`type+model` etc.) resolve
  through the single-sourced frozensets named above. None is extractable logic.

### Other positives

- **Relay-shaped predicate cluster is principled, not duplication (folder-pass
  focus #1).** Within `types/` there are two distinct predicates with different
  inputs, different lifecycle phase, and mutually-cross-referencing docstrings:
  - `base.py::_is_relay_shaped(cls, interfaces)`
    (`types/base.py #"def _is_relay_shaped"`, lines 446-457):
    `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`.
    Runs **pre-`__bases__`-injection** at class-creation / annotation-synthesis
    time (`_validate_meta` :1084, `__init_subclass__` :570, `_build_annotations`
    :1558), so it MUST scan the validated `Meta.interfaces` tuple in addition to
    `cls` itself — the `relay.Node` base is not yet in the MRO at this timing.
  - `relay.py::implements_relay_node(type_cls)`
    (`types/relay.py #"def implements_relay_node"`, lines 52-62):
    `issubclass(type_cls, relay.Node)`. Runs **post-`__bases__`-injection** in
    finalizer Phase 2.5 (and registry/filters), where the interface is already in
    the MRO so the one-arg subclass check is complete.
  Each docstring explicitly names the other and explains the timing split
  (`_is_relay_shaped` "runs … at different timings (class-creation-time vs.
  annotation-synthesis-time)"; `implements_relay_node` "Distinct from Slice 3's
  tuple-membership check … which runs pre-base-injection at collection time").
  Merging them would be a correctness regression: `_is_relay_shaped` cannot drop
  the `interfaces` scan, and `implements_relay_node` cannot afford the two-arg
  signature at its 11 post-injection call sites. **Verdict: principled — do NOT
  consolidate within types/.** The cross-folder re-spell
  `inspect_django_type.py::_is_suppressed_relay_pk`
  (`management/commands/inspect_django_type.py:209-212`) inlines the exact
  `_is_relay_shaped` body, and the package-wide "shared field-guards home" question
  (also forwarded from `list_field.py`, which imports `_is_relay_shaped` directly
  at `list_field.py:19/121`) is a PROJECT-pass concern — forwarded to
  `rev-django_strawberry_framework.md`, not resolved here.
- **`relation_connections` producer/consumer contract is folder-coherent
  (focus #2).** `definition.py` owns the slot
  (`relation_connections: dict[str, str] | None = None`); finalizer.py is the
  single writer (`_record_relation_connection`, called only from Phase-2.5
  `_synthesize_relation_connections`, recording `generated -> relation_field_name`
  exactly when a sibling is attached — suppressed shapes record nothing, so keys
  are precisely the connections that exist). Two read-only consumers agree on
  `None`-coercion: `optimizer/walker.py #"relation_connections = getattr"`
  (line 284) does a forward `snake_case(sel.name) in relation_connections` lookup
  (gen → rel) for windowed planning, and
  `management/commands/inspect_django_type.py #"definition.relation_connections or"`
  (lines 262-263) does the inverted `gen for gen, rel … if rel == field.name`
  lookup for introspection rendering. Forward-vs-inverted is correct for each
  consumer's need; both treat the absent slot as empty. The walker keys the PRIMARY
  definition while synthesis records the iterated `type_cls` — the documented
  Decision-3 divergence (a secondary type's connection is never windowed), verified
  honest in the per-file passes.
- **GlobalID strategy threading is single-owner-per-concern (focus #3).** base.py
  owns the strategy *vocabulary* (`STRING_GLOBALID_STRATEGIES` /
  `DEFAULT_GLOBALID_STRATEGY`) and the shared `_validate_globalid_strategy`;
  definition.py owns the *storage slot* (`effective_globalid_strategy`, default
  `None`, definition.py:173); relay.py *stamps* it (custom branch relay.py:597 /
  classification branch relay.py:605, mutually exclusive per call) and *reads* it in
  `encode_typename` / `decode_global_id`; finalizer.py *reads* the stamped value
  post-Phase-2.5 for `_audit_model_label_routing` /
  `_warn_model_label_secondary_collapse` (finalizer.py:239/257/293). The phase
  ordering (stamp in 2.5 → audits read complete data → Phase 3 flips `finalized`) is
  the invariant the finalizer review verified. No write-site sprawl, no
  read-before-stamp.
- **Error-handling discipline is uniform and principled (focus #4).** Every
  build-time / consumer-configuration failure across base / converters / finalizer
  / relay raises `ConfigurationError`. The lone `OptimizerError` in the folder is
  `resolvers.py::_check_n1`'s runtime N+1-strictness raise
  (`types/resolvers.py #"Unplanned N+1"`) — correctly an optimizer concern (the
  `optimizer/` folder owns `OptimizerError` per field_meta/plans), not config. The
  config-vs-runtime boundary is the discriminator; no drift.
- **`types/__init__.py` export surface is otherwise correct.** `__all__` carries
  exactly the three intended consumer-facing re-exports (`DjangoType`,
  `SyncMisuseError`, `finalize_django_types`); the internal helpers named in the
  docstring (`convert_scalar`, `convert_choices_to_enum`, `_make_relation_resolver`,
  `_attach_relation_resolvers`) are correctly withheld and reachable only via dotted
  submodule paths. `SyncMisuseError`'s re-export chain (`utils/querysets.py` origin
  → `types/relay.py` explicit `as`-alias re-export → `types/__init__.py` →
  top-level `__init__.py`) is consistent at every hop. The only `__init__.py`
  defects are the two docstring-accuracy Lows above.
- **One-way dependency direction holds at module load.** No module-top import from
  `optimizer/` or `utils/` reaches back into `types/`; the single `optimizer →
  types` edge is the documented in-function lazy fallback at `walker.py:801` (L2),
  and `registry.py`'s `types` imports are TYPE_CHECKING-only (`registry.py:30-31`)
  plus in-function (`implements_relay_node` at `registry.py:373`). No
  circular-import risk at package init.

### Summary

The `types/` folder is in excellent shape. All seven modules are individually
`verified`; the folder pass confirms they compose coherently. The relay-shaped
predicate cluster is **principled, not act-now folder DRY**: `_is_relay_shaped`
(base.py, pre-`__bases__`-injection, two-arg, scans `Meta.interfaces`) and
`implements_relay_node` (relay.py, post-injection, one-arg subclass check) are
genuinely different inputs/semantics at different lifecycle phases with
cross-referencing docstrings — merging would regress correctness. The
`relation_connections` slot (owned by definition.py, single-written by finalizer
Phase-2.5, dual-read by walker forward and inspect inverted, both `None`-coercing)
is folder-coherent; the GlobalID strategy threading splits vocabulary (base) /
storage (definition) / stamp+encode+decode (relay) / audit-read (finalizer)
cleanly; and the `ConfigurationError`-for-config / `OptimizerError`-for-runtime
boundary is uniform with no drift. Two real Lows, both in the folder-pass-owned
`types/__init__.py` module docstring: "Both re-exports" lags the three-symbol
`__all__` (omits `SyncMisuseError`), and the absolute "optimizer must not import
back from types/" rule is contradicted by the sanctioned lazy back-edge at
`walker.py:801`. Both warrant a real `__init__.py` docstring edit → standard cycle
(`under-review`), not shape #5. **Cross-folder forwards to the project pass
`rev-django_strawberry_framework.md`:** (a) the relay-predicate re-spell
`inspect_django_type.py::_is_suppressed_relay_pk` + the shared field-guards-home
question (also forwarded from `list_field.py`); (b) the lazy `optimizer → types`
back-edge and whether the dependency-direction narrative should canonize it; plus
the standing optimizer anonymous-inline-fragment High already carried in worker
memory.

---

## Fix report (Worker 2)

Consolidated single-spawn (docstring-only, no logic change — qualifies under the
"only in-cycle edit is module-docstring sentences" shape). Logic + comment +
changelog disposition collapsed into one pass; bare `Status: fix-implemented` set
once.

### Files touched
- `django_strawberry_framework/types/__init__.py` (module docstring only) — fixed
  both Lows. **L1:** the "Both re-exports (``DjangoType`` and
  ``finalize_django_types``)" sentence now enumerates all three members of the live
  `__all__` (`("DjangoType", "SyncMisuseError", "finalize_django_types")`):
  "The three re-exports (``DjangoType``, ``SyncMisuseError``, and
  ``finalize_django_types``) are also exposed at the top-level package…". **L2:**
  the absolute "The optimizer subpackage must not import back from ``types/``" rule
  was softened to scope the prohibition to module-import time and name the one
  sanctioned exception — the in-function lazy read at `optimizer/walker.py`'s
  ``origin_has_custom_id_resolver`` fallback (imports ``types.definition`` inside the
  function to dodge the package-init cycle; a leaf read, not module-load coupling).
  The closing `..utils` inverse-direction clause changed "forbidden by the same rule"
  → "bounded by the same rule" so the one-way claim stays consistent with the new
  exception wording. No logic change; `__all__` and the import block are untouched.

### Premise confirmation (both verified against source before editing)
- **L1 — the three `__all__` members:** `types/__init__.py` line 29 carries
  `__all__ = ("DjangoType", "SyncMisuseError", "finalize_django_types")`; the import
  block (lines 25-27) is `from .base import DjangoType` / `from .finalizer import
  finalize_django_types` / `from .relay import SyncMisuseError`. The old docstring's
  "Both"/two enumeration omitted `SyncMisuseError`. Confirmed three symbols.
- **L2 — the `walker.py:801` back-edge:** read `optimizer/walker.py` lines 793-803.
  `origin_has_custom_id_resolver` is imported in-function (`from ..types.definition
  import origin_has_custom_id_resolver`, line 801) for the definition-less
  custom-`id`-resolver fallback, immediately under an explicit cycle-dodge comment
  (lines 798-800: "Lazy import: ``types.definition`` pulls in
  ``optimizer.field_meta`` at module load… importing it at the top of the walker
  risks an import-time cycle"). It is a leaf-function read (`return
  origin_has_custom_id_resolver(target_type, target_pk_name)`), so the CODE is
  correct — only the docstring's absolutism was wrong, exactly as the artifact
  framed it. Did not soften beyond reality: the rule still holds one-way at
  module-import time and the exception is named precisely as the single permitted edge.

### Tests added or updated
- None. Docstring-only edit, no behaviour change, nothing to pin (no logic, no
  contract, no error string affected).

### Validation run
- `uv run ruff format .` — pass / no-changes (265 files unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).
- No pytest (per AGENTS.md / worker-2 hard rules). `uv.lock` not modified
  (`git status --short uv.lock` clean).

### Notes for Worker 3
- No shadow file used (edit was a localised docstring rewrite; the artifact's own
  citations were sufficient and were re-confirmed against live source as above).
- No false-premise rejections — both Lows confirmed true against source.
- `git diff` for `types/__init__.py` is docstring-only (module docstring lines
  inside the opening `"""…"""`); `from .base import DjangoType` is the first line
  after the docstring and is unchanged. The whole-tree `git diff --stat` vs baseline
  `0872a20` is large because the baseline predates prior worker cycles' merges
  (concurrent/prior work, AGENTS.md #33) — my contribution is `types/__init__.py`
  only.
- L2's cross-folder forward (the dependency-direction narrative / whether to canonize
  the lazy back-edge) stays routed to `rev-django_strawberry_framework.md` (project
  pass) per the artifact — not in scope here; this cycle only fixes the local
  docstring's accuracy.

---

## Verification (Worker 3)

### Logic verification outcome
NO logic changed. `git diff 0872a20 -- types/__init__.py` is module-docstring-only:
every `[-+]` hunk sits inside the opening `"""…"""`; the import block
(`from .base import DjangoType` / `.finalizer import finalize_django_types` /
`.relay import SyncMisuseError`, lines 31-33) and `__all__` (line 35) are
byte-unchanged. Both Lows are themselves docstring edits, so logic+comment collapse.

- **L1 — three `__all__` members named:** read the live `__all__` (line 35) =
  `("DjangoType", "SyncMisuseError", "finalize_django_types")`. Docstring line 11-12
  now reads "The three re-exports (``DjangoType``, ``SyncMisuseError``, and
  ``finalize_django_types``)" — all three present, count corrected from "Both". PASS.
- **L2 — softened dependency-direction wording accurate:** confirmed the back-edge is
  in-function/leaf, not a module-top import. `optimizer/walker.py:801`
  `from ..types.definition import origin_has_custom_id_resolver` sits INSIDE the
  fallback fn, below the registry hot-path early-return (:795-797), under the explicit
  cycle-dodge comment (:798-800), and is a leaf read (`return
  origin_has_custom_id_resolver(...)` :803). The new docstring scopes the prohibition
  to "one-way at module-import time" + names this single sanctioned exception
  precisely (lazy, cycle-dodging, leaf read), and flips the `..utils` inverse clause
  "forbidden"→"bounded" to keep the one-way claim consistent. No overclaim. PASS.

### DRY findings disposition
Relay-predicate cluster verdict "principled — do NOT consolidate within types/"
(`_is_relay_shaped` two-arg pre-injection vs `implements_relay_node` one-arg
post-injection, cross-referencing docstrings, merge = correctness regression) upheld.
The 7 defer-with-trigger DRY bullets all stayed deferred (triggers unchanged/unfired).
Cross-folder forwards recorded for the project pass (`rev-django_strawberry_framework.md`):
(a) relay-predicate re-spell `inspect_django_type.py::_is_suppressed_relay_pk` + the
shared field-guards-home question (also from `list_field.py`); (b) the lazy
`optimizer → types` back-edge and whether the dependency-direction narrative canonizes
it; (c) the standing optimizer anonymous-inline-fragment High (worker memory).

### Temp test verification
- None used. Docstring-only diff with no behaviour change; logic/contract/error
  strings untouched, nothing to pin or probe.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
types/ folder-pass checklist box. Diff confirmed docstring-only (import block +
`__all__` byte-unchanged), L1 names all three `__all__` members, L2 back-edge
correctly described as in-function/leaf, changelog Not-warranted (empty diff, both
citations), ruff clean.

---

## Comment/docstring pass

Consolidated into the single spawn above (both Lows are themselves docstring edits,
so the logic pass and the comment pass are one and the same — there is no separate
logic surface for Worker 3 to bless before the docstring wording can be known).

### Files touched
- `django_strawberry_framework/types/__init__.py` (module docstring) — same edit as
  the Fix report: L1 three-symbol enumeration, L2 softened dependency-direction rule
  naming the sanctioned `walker.py` lazy back-edge.

### Per-finding dispositions
- Low 1 (L1, "Both re-exports" lags three-symbol `__all__`): fixed — docstring now
  enumerates `DjangoType`, `SyncMisuseError`, `finalize_django_types`.
- Low 2 (L2, absolute "optimizer must not import back from types/" contradicted by
  sanctioned lazy back-edge): fixed — rule scoped to module-import time + names the
  single permitted edge (`optimizer/walker.py`'s in-function
  `origin_has_custom_id_resolver` fallback). No overclaim: the back-edge is described
  exactly as it exists (in-function, cycle-dodging, leaf read).

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
Cross-folder forwards (relay-predicate re-spell; the dependency-direction-narrative
canonization question) remain routed to the project pass per the Summary — untouched
here.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
The cycle's only edit is internal module-docstring polish — re-aligning a re-export
count to the live `__all__` and softening an over-absolute dependency-direction
sentence to match a long-standing sanctioned in-function lazy import. No
consumer-visible behaviour, public symbol, typed-error contract, or warning text
changes. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed")
AND the active review plan's silence on any changelog authorization for this cycle
(the dispatch prompt explicitly forbids touching CHANGELOG.md and a per-folder cycle
is never the authorising scope — CHANGELOG drift forwards to the project pass).

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log
