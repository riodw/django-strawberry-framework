# Review: `django_strawberry_framework/utils/relations.py`

Status: verified

## DRY analysis

- None — this module IS the single-source for the relation-shape contract consumed package-wide. `relation_kind` / `is_many_side_relation_kind` / `instance_accessor` / the `RelationKind` alias / `MANY_SIDE_RELATION_KINDS` frozenset are each declared exactly once here and imported (never re-spelled) by every consumer: optimizer (`walker.py:22`, `field_meta.py:26`, `plans.py:45`), types (`finalizer.py:65`, `relations.py:24`, `resolvers.py:50`, `base.py:1597`), orders (`sets.py:49`), the management command (`inspect_django_type.py`), and the `utils/__init__.py:29` re-export. The membership-test predicate `is_many_side_relation_kind` deliberately wraps the frozenset so callers never spell the `{"many", "reverse_many_to_one"}` set inline (`field_meta.py:136`, `walker.py:142,732`, `orders/sets.py:83`, `resolvers.py:241`). Re-consolidating a consolidation point is net-negative.

## High:

None.

## Medium:

None.

## Low:

### `instance_accessor` is consumed across folders but is not in `utils/__init__.py.__all__`

`instance_accessor` is a public-shaped helper imported by three subsystems
(`types/finalizer.py:490`, `types/resolvers.py:327`, `optimizer/walker.py:565,712,1467`),
yet `utils/__init__.py.__all__` re-exports only `RelationKind` /
`is_many_side_relation_kind` / `relation_kind` and omits it. This is a deliberate,
internally-consistent choice — every consumer imports `instance_accessor` directly
from `..utils.relations`, and the `utils` package docstring's `relations` bullet
also lists only the three re-exported symbols, so there is no drift between the
`__all__`, the docstring, and the call sites. The asymmetry is harmless today.

Forward-looking, deferred: if a future cross-folder consumer starts importing
`instance_accessor` via the `utils` package root (rather than the `.relations`
submodule) — the way the other three relation symbols are imported — promote
`instance_accessor` into `utils/__init__.py.__all__` and the package docstring's
`relations` bullet in the same change so the public surface stays coherent. No
action now: the current "submodule-direct for `instance_accessor`, package-root for
the other three" split is consistent across all call sites and both doc surfaces.

### Final `return field.name` is the only undefaulted reflective read

`instance_accessor`'s first two tiers use `getattr(field, ..., None)` and gate on
`is not None`; the third tier is a bare `field.name` with a `# type: ignore[attr-defined]`
(`relations.py:117`). For the documented inputs (FieldMeta with `accessor_name`,
raw reverse descriptor with `get_accessor_name`, forward field / test double with
`name`) this is correct and fails loudly — a shape lacking all three attributes
raises `AttributeError` at the call site rather than returning a wrong accessor
silently. That loud-failure-at-call-site is the right contract for an internal
helper whose every caller hands in a real Django field or `FieldMeta`; do not
soften it to a defaulted `getattr`. No action; recorded for completeness.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical owner; it reuses nothing because everyone reuses it. `is_many_side_relation_kind` (`relations.py:80-82`) wraps the single `MANY_SIDE_RELATION_KINDS` frozenset (`relations.py:14-16`) so the `{"many", "reverse_many_to_one"}` set is spelled exactly once and the 5 membership call sites stay literal-free.
- **New helpers considered.** None warranted. The `_RelationFieldLike` Protocol (`relations.py:19-32`) already factors the four-flag read contract into one documented shape; the `getattr(..., False)` defenses in `relation_kind` are intentionally retained alongside the narrower annotation (the docstring states this explicitly).
- **Duplication risk in the current file.** The repeated kind literals flagged by the static helper (`reverse_many_to_one` ×3, `reverse_one_to_one` ×2, `forward_single` ×2, `auto_created` ×2) are `RelationKind` Literal members / Django flag names appearing in the classifier body, the `RelationKind` alias declaration, and the docstring — they are the enumerated vocabulary itself, not dispatch keys that could be hoisted. Hoisting Django's own attribute name `auto_created` into a constant would obscure, not clarify.

### Other positives

- **Classification correctness verified branch-by-branch against Django descriptor flags.** Forward `ManyToManyField` (`many_to_many=True`) → `"many"` (line 69). Reverse FK `ManyToOneRel` (`one_to_many=True` + `auto_created=True`) → `"reverse_many_to_one"` (line 72). Reverse `OneToOneRel` (`one_to_one=True` + `auto_created=True`) → `"reverse_one_to_one"` (line 75). Forward `ForeignKey` (`one_to_many=False`/`one_to_one=False`) and forward `OneToOneField` (`one_to_one=True`, `auto_created=False`) both fall through to `"forward_single"` (line 77). The defensive `one_to_many=True` + no `auto_created` → `"many"` mapping (line 74) is unreachable from stock Django but explicitly test-pinned.
- **Every branch has a dedicated unit test.** `tests/utils/test_relations.py` pins all five `relation_kind` outcomes (incl. the defensive `one_to_many`-without-`auto_created` fallback and forward-O2O-vs-reverse-O2O split), the `RelationKind` Literal membership for `PendingRelation`, the `utils.__init__` re-export identity (`is` checks), the `is_many_side_relation_kind` truth table incl. `None`, and all three `instance_accessor` tiers (precomputed slot wins, reverse `get_accessor_name`, forward `name` fallback).
- **`is_many_side_relation_kind` accepts `RelationKind | None`** and returns `False` for `None` via frozenset membership — no special-casing needed, and the type signature documents that callers may pass an un-classified `None`.
- **`instance_accessor` docstring is exceptionally precise** about the Round-4 S3 reverse-relation `name` vs `get_accessor_name()` split (query name `"book"` vs instance attr `"book_set"`), why fakeshop fixtures masked it, and the three-tier read order matching the two field shapes the package passes around. The optimizer (`walker.py:544`) and `field_meta.py:103` cross-reference this helper as the authority for the instance-vs-key vocabulary distinction.
- **Pure-stdlib imports** (`typing` only); zero Django/ORM imports, zero import-time side effects, no circular-import risk. The Protocol is structural so the module never imports Django's `ForeignObjectRel` / `ManyToOneRel` concrete types.
- **No GLOSSARY drift.** `docs/GLOSSARY.md` mentions none of this module's symbols, so there is nothing to keep in sync.

### Summary

`utils/relations.py` is byte-identical to baseline `14910230` (empty `git log
14910230..HEAD` and empty `git diff HEAD`). It is the single-source relation-shape
classifier consumed by the optimizer, types, and orders subsystems; the
classification logic is correct across forward M2M / reverse FK / reverse O2O /
forward FK / forward O2O, with the one defensive non-Django branch explicitly
test-pinned. Reflective `_meta`-flag access is safe (defaulted `getattr` everywhere
the shape may legitimately vary; the one bare `field.name` read fails loudly at the
call site for the internal-only contract). Typing is clean (`Protocol` read
contract + `Literal`/`TypeAlias` for `RelationKind`). No High or Medium findings;
two forward-looking Lows recorded with explicit triggers, neither actionable now.
No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, no changes (270 files left unchanged).
- `uv run ruff check .` — pass, all checks passed.

### Notes for Worker 3
- Both Lows are forward-looking with explicit triggers and require no action this cycle:
  - **`instance_accessor` not in `__all__`** — deferred; trigger = a cross-folder consumer imports it via the `utils` package root instead of the `.relations` submodule. Current submodule-direct import is consistent across all 3 consumers and both doc surfaces (the `__all__` and the package docstring's `relations` bullet both list only the three re-exported symbols).
  - **Bare `return field.name` final tier** — no action; the loud `AttributeError`-at-call-site is the correct contract for this internal helper. Not a softening candidate.
- No GLOSSARY-only fix in scope (GLOSSARY mentions none of this module's symbols).
- Source byte-identical to baseline `14910230` (empty `git log`/`git diff HEAD`).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits — the module docstring, the `_RelationFieldLike` contract docstring, the `relation_kind` branch-by-branch docstring (incl. the defensive-fallback test-pin reference), and the `instance_accessor` three-tier docstring are all accurate against the current implementation and the live Django descriptor semantics. No stale TODOs, no spec-anchor drift.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no source change this cycle (review-only, empty diff). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_10.md` (silent on changelog entries for review cycles), no changelog entry is warranted.

---

## Verification (Worker 3)

### Logic verification outcome

No-source-edit cycle (shape #5), so no fix to verify — instead the H0/M0/L2
review is confirmed correct against live source.

- **Classification re-derived branch-by-branch, NOT trusted from the artifact.**
  Ran every relation shape through the exact production branch order
  (`utils/relations.py::relation_kind`) using the Django descriptor flag truth
  table: forward FK (all flags False) → `forward_single`; forward O2O
  (`one_to_one=True`, `auto_created=False`) → `forward_single`; forward M2M
  (`many_to_many=True`) → `many`; reverse FK / `ManyToOneRel`
  (`one_to_many=True`+`auto_created=True`) → `reverse_many_to_one`; reverse O2O /
  `OneToOneRel` (`one_to_one=True`+`auto_created=True`) → `reverse_one_to_one`;
  reverse M2M / `ManyToManyRel` (`many_to_many=True`+`auto_created=True`) →
  `many` (short-circuits on the FIRST branch). All match.
- **Many-side predicate is the load-bearing crux (dispatch emphasis) — proven
  correct.** `MANY_SIDE_RELATION_KINDS = {"many","reverse_many_to_one"}`. Every
  list-valued shape (forward M2M, reverse FK, reverse M2M) maps to a kind in
  that frozenset → `is_many_side_relation_kind` returns `True`; every single-row
  shape (forward FK, forward O2O, reverse O2O) maps outside it → `False`;
  `None` → `False` via plain membership. No shape can be mis-sided: a many-side
  relation cannot be classified as single (would mis-shape a field / under-plan
  the optimizer) nor vice versa.
- **GFK absence is correct, not a missed branch.** `GenericForeignKey` is not a
  concrete relation field carrying these four `_meta` flags and is never handed
  to this classifier (handled upstream); there is no GFK path to get wrong here.
- **`_meta` reflection safety confirmed.** `relation_kind` reads all four flags
  through `getattr(..., False)`, so a shape omitting a flag degrades to
  `forward_single` rather than raising. The one bare reflective read
  (`return field.name`, `relations.py` #"return field.name") is the documented
  final tier of `instance_accessor` and fails LOUD (`AttributeError`) at the
  call site for a shape lacking `accessor_name`/`get_accessor_name`/`name` — the
  correct contract for an internal helper; not a silent-wrong-value risk.
- **Both Lows genuine and forward-looking with verbatim triggers.**
  - L1 (`instance_accessor` ∉ `utils/__init__.__all__`): confirmed the `__all__`
    tuple re-exports exactly `RelationKind`/`is_many_side_relation_kind`/
    `relation_kind` and the package docstring's `relations` bullet
    (`utils/__init__.py` #"relations") lists the same three — zero drift. All
    three consumers (`types/resolvers.py:50`, `types/finalizer.py:65`,
    `optimizer/field_meta.py:26`, plus `optimizer/walker.py:22`) import
    `instance_accessor` submodule-direct from `..utils.relations`. Trigger
    (a consumer imports it via the package root) is unmet today. Forward-defer
    sound; not a GLOSSARY-only fix (GLOSSARY mentions none of these symbols).
  - L2 (bare `return field.name` final tier): loud-`AttributeError`-at-call-site
    is the right contract; no-action sound.

### DRY findings disposition

DRY None accepted as a genuine consolidation point. `relation_kind` /
`is_many_side_relation_kind` / `instance_accessor` are each one `def`, imported
(never re-spelled) by optimizer / types / orders. `is_many_side_relation_kind`
wraps the single `MANY_SIDE_RELATION_KINDS` frozenset so the
`{"many","reverse_many_to_one"}` set is literal-free at all membership sites.
Re-consolidating a consolidation point is net-negative.

### Temp test verification

- None — classification re-derived inline against the descriptor truth table
  (no persisted temp file); existing pinned suite serves as the oracle.
- The defensive non-Django branch (`one_to_many=True` without `auto_created` →
  `"many"`) is pinned at
  `tests/utils/test_relations.py::test_relation_kind_classifies_one_to_many_as_many`
  (the docstring-cited name exists, line 35). The `is_many_side` truth table
  incl. `None` is pinned at line 77; all five `relation_kind` outcomes, the
  `RelationKind` Literal membership, the `utils.__init__` re-export `is`-identity,
  and all three `instance_accessor` tiers are each pinned.

### Shape #5 (no-source-edit) terminal checks

- `git diff HEAD -- django_strawberry_framework/utils/relations.py` empty;
  `git log 14910230..HEAD -- <target>` empty. Last-touch `08da9664`
  (2026-06-12) predates HEAD `58ca2def` — content verified by source-read, not
  the (stale) baseline SHA string.
- Every Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle
  pattern.`
- Changelog `Not warranted` cites BOTH AGENTS.md ("Do not update CHANGELOG.md
  unless explicitly instructed") AND active-plan silence;
  `git diff HEAD -- CHANGELOG.md` empty. Internal-only framing honest — module
  has no public-API surface change this cycle.
- `uv run ruff format --check` (target): already formatted. `uv run ruff check`
  (target): all checks passed.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the
`utils/relations.py` checklist box.

---

## Iteration log

(none)
