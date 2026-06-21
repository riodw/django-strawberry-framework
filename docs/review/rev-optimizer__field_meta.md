# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## DRY analysis

- None — the elision predicate, the cardinality-gated nullable rule, and all
  `getattr`-defaulted relation-shape reads are single-sourced in
  `field_meta.py::FieldMeta._from_field_shape`, consumed by both the canonical
  entry point (`field_meta.py::FieldMeta.from_django_field`) and the two
  drift-prone fallback callers — `types/resolvers.py::_field_meta_for_resolver`
  (test-double shape, `is_relation=True`) and
  `optimizer/walker.py::_can_elide_fk_id` (raw-field elision fallback). Relation
  classification, many-side detection, accessor derivation, and composite-PK
  detection are each single-sited in `utils/relations.py`
  (`relation_kind` / `is_many_side_relation_kind` / `instance_accessor` /
  `has_composite_pk`) and consumed here rather than re-derived. There is no
  remaining duplication to consolidate.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The relation-shape vocabulary is read entirely
  through `utils/relations.py` rather than re-derived: `relation_kind(self)` /
  `is_many_side_relation_kind` back the `relation_kind` / `is_many_side`
  properties (`field_meta.py::FieldMeta.relation_kind`,
  `field_meta.py::FieldMeta.is_many_side`), `relation_kind(field)` drives the
  reverse-OneToOne branch of the nullable gate
  (`field_meta.py::FieldMeta._from_field_shape #"reverse_one_to_one"`),
  `instance_accessor(field)` populates `accessor_name`, and
  `has_composite_pk(related_model)` is the shared composite-PK exclusion in the
  `fk_id_elision_eligible` predicate. Each is the canonical single-source helper
  named in its own docstring.
- **New helpers considered.** `_target_pk_name(model)`
  (`field_meta.py::_target_pk_name`) was evaluated as a candidate to fold into
  `_from_field_shape` inline; kept separate because it carries its own
  defensive-`_meta` rationale (the resolver path fabricates `related_model`
  stand-ins without `_meta`) and is the readable name for "concrete pk field
  name or None". No new cross-module helper is warranted — the
  `_from_field_shape` extraction already collapses the only three call sites.
- **Duplication risk in the current file.** `target_field` is read twice
  (for `target_field_name` and `target_field_attname`) but hoisted to a single
  local with an explaining comment
  (`field_meta.py::FieldMeta._from_field_shape #"Read ``target_field`` once"`);
  intentional and minimal.

### Other positives

- **Cardinality-gated nullable rule is correct and ordering-safe.** The
  many-side gate (`is_m2m or is_o2m → False`) precedes the
  `relation_kind(field) == "reverse_one_to_one"` check; the shapes are disjoint
  (a reverse O2O is neither M2M nor reverse-FK), so the precedence cannot
  misclassify. Reverse O2O short-circuits to `True` (related row may be absent);
  every other single relation follows `getattr(field, "null", False)`. This
  defends against `ForeignObjectRel`'s class-level `null=True` default leaking
  through, exactly as the `nullable` field docstring claims.
- **`fk_id_elision_eligible` predicate is conservative and fail-closed.** It
  requires a local FK column (`attname`), a resolved target
  (`related_model is not None`, `target_pk_name is not None`), a PK-pointing FK
  (`target_field_name == target_pk_name`, which excludes non-PK `to_field`
  connectors), forward single cardinality (`not is_m2m`, `not is_o2m`,
  `not auto_created`), and a non-composite target PK
  (`not has_composite_pk(related_model)`). Every disqualifying shape returns
  `False`, never a wrong-data elision.
- **Reflective-access guards are correct.** `from_django_field` raises a typed
  `OptimizerError` naming the bad input when `name`/`is_relation` are absent,
  converting a late deep-walker `AttributeError` into a call-site failure; every
  other attribute read in `_from_field_shape` uses a `getattr` default so the
  four documented input shapes (forward field, reverse FK, M2M, O2O) build
  without per-shape branching.
- **`_from_field_shape` correctly single-sources the two fallback callers.**
  The resolver test-double path (`types/resolvers.py:292`) and the walker
  raw-field elision path (`optimizer/walker.py:870`) both delegate here with
  `is_relation=True`, so the observable `FieldMeta` matches what the canonical
  builder would produce. The `is_relation` parameter is the only axis that
  legitimately diverges between the entry point and the fallbacks, and it is
  passed explicitly.
- **`frozen=True, slots=True` dataclass** matches the "frozen at class-creation
  time" contract — instances cached on `DjangoTypeDefinition.field_map` are
  immutable and memory-lean.
- **File/image work does not touch this module.** The maintainer's recent
  file/image output-column changes live in the scalar/output layer
  (`FIELD_OUTPUT_TYPE_MAP`, `DjangoFileType` / `DjangoImageType` in
  converters/types) and never reach `FieldMeta`, which is purely relation
  metadata. No file/image-specific branch belongs here and none was added.

### Summary

`field_meta.py` is a clean, frozen-dataclass snapshot of a Django field's
optimizer-relevant relation metadata. The cardinality-gated nullable rule, the
fail-closed FK-id-elision predicate, and the defensive reflective reads are all
correct, and the recent maintainer edits (already in HEAD) leave the file in a
sound state — there is no file/image-specific logic here and none should be
added, since `FieldMeta` carries relation shape only. `_from_field_shape` is the
single elision/shape source shared by all three callers, so the walker and
resolver fallbacks cannot drift. Source diff is empty against both the cycle
baseline (`0a1b468d`) and HEAD, GLOSSARY carries no `FieldMeta` entry (private
optimizer symbol — absence is correct, not drift), and no severity-tier findings
exist. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged`.
- `uv run ruff check --fix .` — `All checks passed!`.

### Notes for Worker 3
- No GLOSSARY-only fix in scope: `docs/GLOSSARY.md` carries no `FieldMeta` /
  `from_django_field` / `fk_id_elision_eligible` entry (private optimizer
  symbol); the file/image GLOSSARY entries reference converter/type symbols, not
  `FieldMeta`. Absence is correct, not drift.
- Source diff empty vs both cycle baseline `0a1b468d` and HEAD; maintainer edits
  already landed in HEAD. Verified the cardinality-gated nullable rule,
  the fail-closed `fk_id_elision_eligible` predicate, the `getattr`/`hasattr`
  guards, and the `_from_field_shape` single-sourcing of the resolver
  (`types/resolvers.py:292`) and walker (`optimizer/walker.py:870`) fallbacks.
- All severities `None.`; DRY a single resolved `None —` bullet.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring
edits warranted — the `nullable` field docstring, the `_from_field_shape`
single-sourcing rationale, and the `_target_pk_name` defensive-`_meta` note all
accurately describe current behavior.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source
edit this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly
instructed"; active plan `docs/review/review-0_0_11.md` records no changelog
action for this item).

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit cycle verifying maintainer-committed work already in
HEAD. Zero-edit proof holds two ways: `git diff 0a1b468d -- ...field_meta.py`
empty AND `git show HEAD:...field_meta.py | diff -` IDENTICAL. Target absent
from the owned-paths `--stat` (dirty paths `mutations/resolvers.py`,
`mutations/sets.py`, `utils/querysets.py` are non-target sibling / AGENTS.md #33
concurrent work, informational only since the target diff is clean). All
High/Medium/Low `None.` independently confirmed genuine:

- **Cardinality-gated nullable rule correct and ordering-safe**
  (`field_meta.py::FieldMeta._from_field_shape #"is_m2m or is_o2m"`). The
  many-side gate (`is_m2m or is_o2m -> False`) precedes the
  `relation_kind(field) == "reverse_one_to_one"` check; shapes are disjoint (a
  reverse O2O has `one_to_one=True, auto_created=True` per
  `utils/relations.py::relation_kind` and is neither M2M nor reverse-FK), so
  precedence cannot misclassify. Reverse O2O -> `True`
  (`test_from_django_field_reverse_one_to_one_is_nullable`), every other single
  relation follows `getattr(field, "null", False)` (forward O2O `False`
  `test_from_django_field_one_to_one`; nullable scalar `True`
  `test_from_django_field_nullable_scalar`); many-side forced `False`
  (reverse FK `test_from_django_field_reverse_fk`, reverse M2M
  `test_from_django_field_reverse_many_to_many`, forward M2M
  `test_from_django_field_many_to_many`). Defends against `ForeignObjectRel`'s
  class-level `null=True` default, exactly as the `nullable` docstring claims.
- **`fk_id_elision_eligible` fail-closed incl. composite-pk exclusion.** Every
  disqualifying shape returns `False`; pinned positive (forward FK / forward
  O2O `True`) and negative (scalar, reverse FK, reverse/forward M2M, reverse
  O2O `False`) by the matching tests. Composite-pk exclusion single-sited at
  `utils/relations.py::has_composite_pk` (reads `_meta.pk_fields` len > 1),
  shared by the `FieldMeta` precompute and the walker fallback so they cannot
  disagree.
- **Typed `OptimizerError` on missing `name`/`is_relation`**
  (`field_meta.py::FieldMeta.from_django_field`) — pinned by
  `test_from_django_field_rejects_non_django_input` and
  `test_from_django_field_rejects_partial_shape`.
- **`_from_field_shape` single-sourced across all three callers, cannot drift.**
  Confirmed at source: `from_django_field` (`field_meta.py:165`),
  `types/resolvers.py::_field_meta_for_resolver` (`:292`, `is_relation=True`
  test-double fallback fired only when `not hasattr(field, "is_relation")`),
  and `optimizer/walker.py::_can_elide_fk_id` (`:870`, reads the precomputed
  `fk_id_elision_eligible` slot first via `getattr(..., None)`, falls back to
  the same helper for raw fields). `is_relation` is the only axis that
  legitimately diverges and is passed explicitly.
- **No file/image branch belongs here and none was added.** `grep` confirms no
  file/image symbol in `field_meta.py`; the maintainer's file/image work lives
  in the scalar/output layer only. `FieldMeta` carries relation shape only.

### DRY findings disposition
Single justified `None —` bullet: the elision predicate, the cardinality-gated
nullable rule, and the `getattr`-defaulted relation-shape reads are
single-sourced in `_from_field_shape`; relation classification / many-side /
accessor / composite-pk detection are each single-sited in `utils/relations.py`.
No GLOSSARY-only fix in scope (which would be disqualifying for #5) — verified.

### Temp test verification
None used; logic confirmed against the existing permanent suite
`tests/optimizer/test_field_meta.py` (every `None.` claim maps to a named test).

### GLOSSARY / #5-gate
Genuine #5. `grep -ni "FieldMeta\|from_django_field\|fk_id_elision"` over
`docs/GLOSSARY.md` returns only one `fk_id_elision` hit (line 588) referencing
the optimizer plan's `dst_optimizer_plan.fk_id_elisions` stash — the optimizer's
*use* of elisions, not the `FieldMeta` symbol. `FieldMeta` is a private
optimizer symbol with no public-contract entry; absence is correct, not drift.

### Changelog disposition
`git diff -- CHANGELOG.md` empty. "Not warranted" cites BOTH AGENTS.md and the
active plan's silence — both present, internal-only framing matches the empty
source diff. Accepted.

### Validation
`uv run ruff format --check` (1 file already formatted) + `uv run ruff check`
(All checks passed!) on `field_meta.py`.

### Verification outcome
cycle accepted; verified — sets top-level `Status: verified` AND marks the
`optimizer/field_meta.py` checkbox in `docs/review/review-0_0_11.md`.
