# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## DRY analysis

- Existing patterns reused: `DjangoType.__init_subclass__` builds the canonical field map once from selected Django fields and mirrors it for current optimizer readers at `django_strawberry_framework/types/base.py:90-142`; `DjangoTypeDefinition.field_map` is the definition-backed storage slot at `django_strawberry_framework/types/definition.py:14-27`; invalid optimizer-shape failures use the package optimizer exception declared at `django_strawberry_framework/exceptions.py:37-43`.
- New helpers a fix might justify: add one `FieldMeta.nullable` or `FieldMeta.relation_nullable` attribute that owns "GraphQL relation may be null" semantics and serves the anchored readers in `django_strawberry_framework/types/converters.py:222-234` and `django_strawberry_framework/types/base.py:604-624`. If this stays as a raw-Django `null` flag instead, a small method/property should still combine it with reverse-OneToOne nullability for callers.
- Duplication risk in the current file: the module claims to be the single source of truth for "relation cardinality + nullable + attname" at `django_strawberry_framework/optimizer/field_meta.py:3-17`, but the dataclass has no nullable field at `django_strawberry_framework/optimizer/field_meta.py:93-103` and `from_django_field` never captures `field.null` at `django_strawberry_framework/optimizer/field_meta.py:130-142`. The exact same nullable derivation remains duplicated in `django_strawberry_framework/types/converters.py:229-234` and `django_strawberry_framework/types/base.py:616-624`.

## High:

None.

## Medium:

### FieldMeta omits nullable despite owning the nullable SSoT contract

`FieldMeta` is documented as the canonical source for relation cardinality, nullability, and connector names, and the `types/` TODO anchors explicitly plan to migrate nullable derivation to it. Today the dataclass stores cardinality, `attname`, target columns, and reverse connector data, but not `field.null` or the package's effective relation-nullability rule. That means the planned DRY migration cannot actually remove the duplicate `kind == "reverse_one_to_one" or getattr(field, "null", False)` logic from the type layer; it would still need to re-derive nullable state from raw Django fields or partial `FieldMeta` flags. Add a nullable value to `FieldMeta`, populate it in `from_django_field`, and pin it with tests for scalar `null=True`, forward non-null relations, and reverse OneToOne nullability.

```django_strawberry_framework/optimizer/field_meta.py:3:17
``FieldMeta`` is the canonical single source of truth for relation
shape across the package: ``is_relation``, cardinality flags
(``many_to_many`` / ``one_to_many`` / ``one_to_one``), ``attname``,
``related_model``, and the FK target columns. Every consumer of
"relation cardinality + nullable + attname" should read from a
``FieldMeta`` instance
```

```django_strawberry_framework/optimizer/field_meta.py:93:103
name: str
is_relation: bool = False
many_to_many: bool = False
one_to_many: bool = False
one_to_one: bool = False
related_model: type[models.Model] | None = None
attname: str | None = None
target_field_name: str | None = None
target_field_attname: str | None = None
reverse_connector_attname: str | None = None
auto_created: bool = False
```

```django_strawberry_framework/types/base.py:610:624
# TODO(spec-fieldmeta-ssot): the ``nullable`` derivation inlines
# ``kind == "reverse_one_to_one" or bool(getattr(field, "null",
# False))`` instead of reading from a ``FieldMeta`` already built
# for ``field`` at the call site.
kind = relation_kind(field)
return PendingRelation(
    ...
    nullable=kind == "reverse_one_to_one" or bool(getattr(field, "null", False)),
)
```

## Low:

None.

## What looks solid

- Required static helper was run with `python scripts/review_inspect.py django_strawberry_framework/optimizer/field_meta.py --output-dir docs/review/shadow --stdout`; it reported no control-flow hotspots and no repeated string literals.
- `FieldMeta` is immutable and slot-backed, so cached metadata cannot be mutated accidentally after class creation.
- `from_django_field` centralizes connector metadata for forward relations, reverse FK attachment, and FK target columns in one place.
- The guard for non-field inputs converts malformed helper calls into a typed `OptimizerError` instead of leaking an arbitrary late `AttributeError`.

### Summary

The file is small and mostly doing the right centralization work, but its SSoT contract has one missing piece: nullable semantics are promised here and already referenced by sibling TODOs, while the stored metadata cannot express them. Fixing that keeps the future field-meta consolidation genuinely DRY instead of moving the duplicate nullable derivation to another layer.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/field_meta.py` — added `FieldMeta.nullable` and populated it in `from_django_field` from the shared relation-kind classifier plus Django's raw `field.null`, so reverse OneToOne descriptors are effectively nullable while non-null forward relations remain non-null.
- `tests/optimizer/test_field_meta.py` — added/pinned nullable metadata coverage for scalar `null=True`, non-null forward FK, and reverse OneToOne descriptors.

### Tests added or updated

- `tests/optimizer/test_field_meta.py::test_from_django_field_nullable_scalar` — pins `null=True` scalar fields as `FieldMeta.nullable is True`.
- `tests/optimizer/test_field_meta.py::test_from_django_field_forward_fk` — pins a non-null forward relation as `FieldMeta.nullable is False`.
- `tests/optimizer/test_field_meta.py::test_from_django_field_reverse_one_to_one_is_nullable` — pins reverse OneToOne descriptors as effectively nullable.

### Validation run

- `uv run ruff format .` — passed, 92 files unchanged.
- `uv run ruff check --fix .` — passed.
- `uv run pytest tests/optimizer/test_field_meta.py` — assertions passed, then exited nonzero on the expected repo-wide coverage gate (`total of 58 is less than fail-under=100`) for the focused run.
- `uv run pytest tests/optimizer/test_field_meta.py --no-cov` — passed, 14 tests.

### Notes for Worker 3

- Static helper output was generated under `docs/review/shadow/`; artifact citations use original source line numbers.
- The TODO-anchored readers in `types/converters.py` and `types/base.py` were intentionally left in place per the Worker 2 prompt; this pass only adds the FieldMeta-owned value they can migrate to later.

---

## Verification (Worker 3)

### Logic verification outcome

Logic accepted. The Medium finding is addressed by adding `FieldMeta.nullable` and populating it in `from_django_field` with the same effective rule called out by the artifact: reverse OneToOne descriptors are nullable, otherwise Django `field.null` decides. Importing `relation_kind` from `django_strawberry_framework.utils.relations` is an acceptable dependency direction because `utils` is the existing cross-cutting relation-shape helper layer used by converters/resolvers/optimizer, and it avoids duplicating the classifier locally in `optimizer/field_meta.py`.

The logic pass is not a full cycle acceptance yet. `FieldMeta`'s class docstring `Attributes:` list still omits the newly added `nullable` attribute, so the cycle needs the normal Worker 2 comment/docstring pass before checklist completion.

### DRY findings disposition

Accepted for the logic pass. The nullable rule is now centralized in `FieldMeta` instead of requiring future readers to keep re-deriving `kind == "reverse_one_to_one" or bool(getattr(field, "null", False))`. The existing TODO-anchored readers in `types/converters.py` and `types/base.py` remain intentionally deferred to the folder-level DRY migration noted in the artifact.

### Temp test verification

- Temp test files used: none.
- Disposition: permanent tests were added in `tests/optimizer/test_field_meta.py`.

### Verification outcome

logic accepted; awaiting comment pass

Validation run by Worker 3:

- `uv run pytest tests/optimizer/test_field_meta.py --no-cov` — passed, 14 tests.
- `uv run ruff format --check django_strawberry_framework/optimizer/field_meta.py tests/optimizer/test_field_meta.py` — passed.
- `uv run ruff check django_strawberry_framework/optimizer/field_meta.py tests/optimizer/test_field_meta.py` — passed.

---

## Comment/docstring pass

Worker 2 updated stale docstring coverage for the accepted `FieldMeta.nullable` addition.

### Files touched

- `django_strawberry_framework/optimizer/field_meta.py` — added `nullable` to the module-level canonical metadata list and to the `FieldMeta` attributes docstring, including the effective reverse OneToOne nullability rule where the related row may be absent.

### Validation run

- `uv run ruff format .` — passed, 92 files unchanged.
- `uv run ruff check --fix .` — passed.

### Notes for Worker 3

- No logic or test changes were made in this pass.
- `CHANGELOG.md` was not edited; changelog disposition remains pending until Worker 3 accepts the comment/docstring pass.

---

## Changelog disposition

Changelog edit is warranted: adding `FieldMeta.nullable` is package-visible optimizer metadata that affects
the public review record for the 0.0.5 cycle and should be mentioned when the maintainer prepares the release
notes.

No `CHANGELOG.md` edit was made in this pass because the active plan and maintainer instructions did not
explicitly authorize Worker 2 to edit the changelog. The disposition is recorded here for maintainer follow-up.

---

## Final verification (Worker 3)

### Verification outcome

cycle accepted; verified

### Notes

Logic, DRY disposition, comment/docstring updates, focused validation, and changelog disposition are accepted.

---

## Iteration log

- Worker 3: comments accepted; awaiting changelog disposition. Top-level status remains `fix-implemented` and the plan checklist remains open.
- Worker 3: cycle accepted; verified. Logic, DRY disposition, comment/docstring updates, focused validation, and changelog disposition are accepted.
