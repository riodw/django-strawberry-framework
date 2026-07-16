# DRY review: `django_strawberry_framework/forms/__init__.py`

Status: verified

## System trace

`forms/__init__.py` is the form-mutations subpackage public entry point
(spec-038). It owns exactly one rule: which names are the curated
`django_strawberry_framework.forms` consumer surface. That rule is stated
once as a pair of eager re-exports from `forms/sets.py`
(`DjangoFormMutation`, `DjangoModelFormMutation`) backed 1:1 by
`__all__`. The module defines no functions, classes, registries, caches,
or lifecycle callbacks.

Connected behavior examined:

- `forms/sets.py` — defines both bases, their metaclasses / `Meta`
  validation, the plain-form declaration registry
  (`register_form_mutation` / `iter_form_mutations` /
  `clear_form_mutation_registry`), the shape-build cache, and
  `bind_form_mutations()`. Sibling file item still open; traced only as
  the re-export target and as the home of framework-internal names this
  `__init__` deliberately omits.
- `forms/converter.py`, `forms/inputs.py`, `forms/resolvers.py` —
  sibling implementation modules named in the package docstring.
  Converter / inputs / resolvers own conversion, generated-input
  lifecycle, and the sync+async write pipeline. None of their symbols
  are re-exported here. Finalizer reaches `bind_form_mutations` via
  `types/finalizer.py` → `forms.sets` (dotted submodule path), never
  through this `__init__`. `mutations/fields.py` reaches
  `iter_form_mutations` the same way.
- Package root `django_strawberry_framework/__init__.py` — eagerly
  imports both form bases from `.forms` and lists them in root
  `__all__` (always-on write surface, beside `DjangoMutation`). This is
  the intentional dual-path facade: root for the default recipe,
  subpackage for namespace-qualified imports. Identity is pinned by
  `tests/forms/test_sets.py` (`root is forms` object identity + both
  names in root `__all__`). Contrast: `auth/` and `extensions/` stay
  off the root by design; `SerializerMutation` is root-lazy / absent
  from `__all__` because DRF is soft.
- Sibling package markers — `mutations/__init__.py` is the closest
  twin (eager re-export + typed `__all__` tuple + slice-era package
  docstring). `filters/` / `orders/` add Decision-11 helpers and
  helper ledgers this file does not need. `rest_framework/__init__.py`
  is a raising soft-dep guard with no `__all__` re-export surface.
  `auth/` / `extensions/` / `utils/` / `testing/` / `types/` /
  `optimizer/` share the eager docstring + import + `__all__` idiom
  with file-specific rationale.
- Consumers — fakeshop `apps/products/schema.py`,
  `apps/library/schema.py`, `apps/scalars/schema.py` import the bases
  from the package root. Package tests import both the root path and
  `django_strawberry_framework.forms` for the identity pin, and reach
  `forms.sets` / `forms.inputs` / `forms.converter` / `forms.resolvers`
  directly for white-box coverage.

Baseline `git diff 87f76ed937e0f2d8e8aa4dfddb4ecfe784d0b96d --
django_strawberry_framework/forms/__init__.py` at review start was empty. The
`converter.py` bullet in the package docstring is repointed by the reverse-map
unification (owned by the `forms/inputs.py` item): the per-input-field
reverse-map record is now `utils/inputs.py::InputFieldSpec` (`target_name` = form
field name), built by `forms/inputs.py`, so this docstring names that owner
instead of describing an `input_attr -> (form_field_name, kind)` record. That is
a one-line navigation-doc update, not an export-surface change; `__all__` and the
re-export pair are untouched.

## Verification

Searches and checks:

- `DjangoFormMutation` / `DjangoModelFormMutation` /
  `from django_strawberry_framework.forms` across the repo — production
  consumers hit the root re-export; the subpackage path is exercised by
  the identity pin and is the documented alternate. No second factory,
  alternate export table, or soft-dep lazy path for these symbols.
- `convert_form_field` / `FormFieldConversion` / `register_form*` —
  converter has no public `register_form_field_converter` twin of the
  DRF `register_serializer_field_converter` surface; advanced/internal
  names stay on leaf modules. Registry / bind / iter helpers live in
  `sets.py` and are imported by finalizer / mutation fields from there.
- Runtime identity check:
  `from django_strawberry_framework import …` and
  `from django_strawberry_framework.forms import …` and
  `forms.sets` are the same objects; `forms.__all__` is exactly the two
  bases; submodule attrs (`converter`, `inputs`, `sets`) appear only as
  transitive package attributes after the `.sets` import, not as curated
  public surface.
- Compared every subpackage `__init__.py` for a shared mutable export
  rule vs a packaging idiom. The three-part eager shape is Python's own
  import/`__all__` mechanism with per-file rationale text — the same
  judgment recorded for `auth/__init__.py` and `extensions/__init__.py`.

Rejected / deferred candidates:

1. **Shared `build_public_exports()` / eager-re-export helper across
   subpackage `__init__` files.** Disproved: shared packaging idiom, not
   a shared change axis. A helper would hide the import/`__all__` 1:1
   correspondence for zero behavioral gain (`DRY.md`: do not optimize
   for fewer lines when ownership is obscured).
2. **Collapse the dual root + `forms` export into one path.** Disproved:
   different product contracts. Root placement marks always-on write
   surface (with `DjangoMutation`); the subpackage path is the
   namespace-qualified alternate. Tests pin object identity so the two
   paths cannot drift into distinct objects. Removing either path would
   break a documented / tested contract this file shares with the root
   (root owns the root `__all__` row; this file owns the subpackage
   surface).
3. **Widen `__all__` to mirror `mutations/__init__.py`'s four-symbol
   surface** (`FieldError`, `DjangoMutationField`, permissions, …).
   Disproved: those symbols are owned by `mutations/` (and
   `DjangoMutationField` already accepts form mutations). Forms has no
   separate field factory and no form-owned error envelope.
   `convert_form_field` / bind / iter helpers are framework-internal or
   advanced leaf imports, not the curated consumer surface GLOSSARY /
   fakeshop schemas advertise.
4. **Re-export `convert_form_field` / `FormFieldConversion` here to
   parallel DRF's root-lazy converter registration surface.** Disproved:
   no public form-field converter registration API exists; DRF's soft
   dependency and consumer-extension story does not apply. Ownership of
   the converter table stays with `forms/converter.py` (sibling item).
5. **Deduplicate the package-docstring module inventory against sibling
   module docstrings / `docs/TREE.md`.** Disproved for this file:
   `__init__` overview is navigation for the subpackage; TREE is
   generated from module docstrings; sibling files own their own
   first-line responsibilities. Collapsing would either starve the
   package overview or edit TREE/sibling owners from the wrong item.
   Slice-era closing sentences ("Slice 2 adds…", "resolvers.py remains
   a Slice 3 concern") match the `mutations/__init__.py` historical
   narrative style and do not encode a second export contract — polish
   deferred, not a consolidation this pass owns.
6. **Align `extensions/__init__.py`'s "eager re-export shape" cross-
   reference list to name `forms/`.** Deferred: that sentence lives in
   `extensions/__init__.py` (or the project integration pass). Editing
   it from this item would still leave an incomplete sibling list, same
   as the rejected auth-side candidate.

No scratch experiment beyond the identity import check: the file is a
pure re-export; import graph and sibling contracts are sufficient.

## Opportunities

None — the target is already the single authoritative public export of
the two form-mutation bases under `django_strawberry_framework.forms`.
It correctly uses the hard-dep eager re-export shape, correctly
participates in the root always-on facade without owning a second copy
of the class bodies, and owns no converter / bind / resolver policy.
Sibling `sets.py` / `converter.py` / `inputs.py` / `resolvers.py` and
the folder `forms/` pass remain the places for implementation and
package-integration DRY work.

## Judgment

No consolidation this file owns. Thin, correctly bounded package marker; the
only in-file change is the one-line docstring repoint of the `converter.py`
reverse-map bullet at `utils/inputs.py::InputFieldSpec`, a downstream navigation
update from the `forms/inputs.py` migration item — the export surface (`__all__`
+ the two eager re-exports) is unchanged. Ready for Worker 2.

## Implementation (Worker 1)

No consolidation edit owned here; the package docstring's `converter.py`
reverse-map bullet is repointed at `utils/inputs.py::InputFieldSpec` as a
downstream doc update from the `forms/inputs.py` migration item (no export-surface
change). Concurrent dirty paths outside
`django_strawberry_framework/forms/__init__.py` left untouched. Plan checkbox not
flipped.

## Independent verification (Worker 2)

Scoped diff vs `ITEM_BASELINE`
`87f76ed937e0f2d8e8aa4dfddb4ecfe784d0b96d` is the single docstring-bullet repoint
described above (export surface unchanged). No consolidation edit in this pass.

Re-traced the consumer surface independently:

- Target owns only the curated `forms` `__all__` pair; class bodies, registries,
  bind, converter, and resolvers live in siblings. Finalizer /
  `mutations/fields.py` reach `bind_form_mutations` / `iter_form_mutations` via
  `forms.sets`, never this marker.
- Runtime: root / `forms` / `forms.sets` object identity holds for both bases;
  `forms.__all__` is exactly those two names. Submodules loaded by the `.sets`
  import (`converter`, `inputs`, `sets`) are package attributes but not curated;
  `resolvers` / `convert_form_field` / `bind_form_mutations` are absent from the
  package object until leaf import.
- Fakeshop schemas (products, library, scalars) and the identity pin in
  `tests/forms/test_sets.py::test_bases_exported_from_package_root` consume the
  dual root + subpackage facade; no alternate factory or lazy soft-dep path
  exists for these hard-dep symbols.

Challenges to rejected candidates (all stand):

1. Shared eager-re-export helper — packaging idiom across `__init__` files, not
   one change axis; a helper would obscure the import/`__all__` 1:1 rule.
2. Collapse dual root + `forms` export — distinct product contracts; identity
   pin forbids divergent objects; root owns the root `__all__` row.
3. Widen `__all__` toward `mutations/` — `FieldError` / `DjangoMutationField` /
   permissions are mutations-owned; form registry/bind/converter names are
   framework-internal leaf imports (sets.py's "public names" wording is for
   registry/finalizer/test call sites, not consumer `__all__`).
4. Re-export converter registration twins — no public form-field converter
   registration API; DRF soft-dep story does not apply.
5. Docstring inventory vs TREE / sibling first lines — navigation vs generated
   TREE vs leaf ownership; polish not a consolidation this file owns.
6. `extensions/__init__.py` cross-ref list omitting `forms/` — lives on the
   extensions item / project pass.

Missed consolidation search: no second export table, no stale dual class body,
no consumer import of an uncurated name that should move into this `__all__`,
and no shared mutable export ledger that this marker should own. No consolidation
owned here beyond the downstream docstring repoint.

Disposition: verified. Plan item checked.
