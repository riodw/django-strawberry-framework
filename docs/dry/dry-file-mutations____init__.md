# DRY review: `django_strawberry_framework/mutations/__init__.py`

Status: verified

## System trace

`mutations/__init__.py` is the model-mutation subpackage public entry point
(spec-036). It owns exactly one rule: which names are the curated
`django_strawberry_framework.mutations` consumer surface. That rule is stated
once as four eager re-exports backed 1:1 by `__all__`:

- `FieldError` ← `mutations/inputs.py`
- `DjangoMutation` ← `mutations/sets.py`
- `DjangoModelPermission` ← `mutations/permissions.py`
- `DjangoMutationField` ← `mutations/fields.py`

The module defines no functions, classes, registries, caches, or lifecycle
callbacks. Sibling modules own generation, Meta validation / bind, write-auth,
the sync+async pipeline, and the field factory. Finalizer reaches
`bind_mutations` via `types/finalizer.py` → `mutations.sets` (dotted submodule
path), never through this `__init__`. Forms / rest_framework / auth reach
leaf modules (`mutations.inputs`, `mutations.sets`, `mutations.resolvers`,
`mutations.permissions`, `mutations.fields`) the same way for shared machinery.

Connected behavior examined:

- Package root `django_strawberry_framework/__init__.py` — eagerly imports the
  same four symbols from `.mutations` and lists them in root `__all__`
  (always-on write surface). Dual-path facade: root for the default recipe,
  subpackage for namespace-qualified imports. Identity pinned by
  `tests/mutations/test_sets.py` (`DjangoMutation` / `DjangoModelPermission`),
  `tests/mutations/test_inputs.py` (`FieldError`), and
  `tests/base/test_init.py` (root `__all__` includes all four).
- Sibling package markers — closest twin is `forms/__init__.py` (thin eager
  re-export + typed `__all__`). `filters/` / `orders/` add Decision-11 helpers
  and helper ledgers this file does not need. `rest_framework/__init__.py` is
  a raising soft-dep guard with no curated `__all__` re-export surface.
- Consumers — fakeshop schemas import from the package root; package tests
  exercise both root and `django_strawberry_framework.mutations` for identity
  pins, and reach leaf modules for white-box coverage.
- Sibling work (out of scope here) — the shared metaclass factory has since
  landed at `mutations/sets` (consumed by `forms/sets`); the plain-form fold →
  `mutations/resolvers` stays deferred. Neither is this marker's concern.

Baseline `git diff f6557d9c1eff1a6ea1a2a1ad3a352ea33ff22b4f --
django_strawberry_framework/mutations/__init__.py` was empty before this pass;
working tree matched baseline for the target.

## Verification

Searches and checks:

- `from django_strawberry_framework.mutations import` / root
  `from .mutations import` across the repo — production consumers hit the root
  re-export; the subpackage path is exercised by identity pins. No second
  factory, alternate export table, or soft-dep lazy path for these hard-dep
  symbols.
- Runtime identity: root / `mutations` / leaf module objects are identical for
  all four curated names; `mutations.__all__` is exactly those four.
  Framework-internal names (`DenyAll`, `iter_mutations`, `register_mutation`,
  `bind_mutations`, `NON_FIELD_ERROR_KEY`) are absent from the package object
  until leaf import and stay out of `__all__`.
- Compared every subpackage `__init__.py` for a shared mutable export rule vs
  a packaging idiom. The three-part eager shape is Python's own import /
  `__all__` mechanism with per-file rationale — same judgment as
  `forms/__init__.py` / `auth/__init__.py` / `extensions/__init__.py`.
- Found in-file knowledge divergence: the package docstring said
  "four-module" while listing five bullets including `permissions.py`
  (Decision 15 write-auth, added beside Decision 4's quartet). The
  four-symbol public surface claim was already correct.

Rejected / deferred candidates:

1. **Shared `build_public_exports()` / eager-re-export helper across
   subpackage `__init__` files.** Disproved: shared packaging idiom, not a
   shared change axis. A helper would hide the import/`__all__` 1:1
   correspondence for zero behavioral gain (`DRY.md`: do not optimize for
   fewer lines when ownership is obscured).
2. **Collapse the dual root + `mutations` export into one path.** Disproved:
   different product contracts. Root placement marks always-on write surface;
   the subpackage path is the namespace-qualified alternate. Identity pins
   forbid divergent objects. Root owns the root `__all__` row; this file owns
   the subpackage surface.
3. **Widen `__all__` with `DenyAll` / `iter_mutations` / `bind_mutations` /
   `NON_FIELD_ERROR_KEY` / resolver helpers.** Disproved: those are
   framework-internal or advanced leaf imports (finalizer, form/DRF flavors,
   white-box tests). Spec-036 Decision 5 freezes the four-symbol consumer
   surface; `tests/base/test_init.py` pins the root list.
4. **Re-export a Decision-11-style `mutation_input_type` helper to mirror
   filters/orders.** Disproved: mutations materialize inputs via
   `Meta` + finalizer bind, not a consumer-facing lazy-annotation helper.
   No second ledger or orphan-check contract lives on this marker.
5. **Align export of `DjangoMutationField` identity pin with the other three
   package-path identity tests.** Deferred polish: root `__all__` already
   pins the name; missing package-path `is` for `DjangoMutationField` is a
   test-coverage nicety owned by `tests/mutations/test_fields.py` if
   desired, not a production duplication this file owns.
6. **Shared metaclass factory / plain-form fold into
   `mutations/sets` / `mutations/resolvers`.** Owned by those modules, not this
   `__init__`: the metaclass factory has since landed at `mutations/sets`; the
   plain-form fold stays deferred to `mutations/resolvers`.

No scratch under `docs/dry/temp-tests/`: import graph + runtime identity were
sufficient.

## Opportunities

**1. Divergent module-count description in the package overview**

- **Repeated responsibility:** how many modules the `mutations/` subpackage
  contains and why `permissions.py` exists beside Decision 4's quartet.
- **Sites:** the opening package docstring ("four-module") vs the five-bullet
  inventory that immediately follows (including `permissions.py`).
- **Evidence:** same overview, two incompatible counts; Decision 4 named
  `inputs` / `sets` / `resolvers` / `fields`, and Slice 2 / Decision 15 added
  `permissions.py` as a fifth module. The four-symbol `__all__` surface was
  already accurate and unchanged.
- **Owner:** the package docstring in this file (the subpackage overview).
- **Consolidation:** rewrite the overview to "five-module" and name Decision 4
  quartet + Decision 15 write-auth; drop stale "This slice…" narrative; point
  the packaging idiom at the closer `forms/__init__.py` twin.
- **Proof:** the five sibling `.py` files on disk and the four-name `__all__`
  tuple immediately below; identity / root-export tests already pin the
  public surface.
- **Risks / non-goals:** do not widen `__all__`; do not edit `forms/__init__.py`
  or standing TREE/GLOSSARY from this item; do not pull sets/resolvers
  consolidations forward.

## Judgment

One in-file knowledge fix (stale four-vs-five module count + slice-era closing
sentence). No further consolidation: the four-symbol export list is already the
single authoritative consumer surface under
`django_strawberry_framework.mutations`, correctly participates in the root
always-on facade without owning class bodies, and owns no bind / resolver /
permission policy. Sibling file items and the folder `mutations/` pass remain
the places for implementation DRY work.

## Implementation (Worker 1)

- **Owner:** package docstring in `mutations/__init__.py`.
- **Migrated:** overview text only — "five-module" + Decision 4 quartet /
  Decision 15 rationale; present-tense four-symbol re-export sentence; idiom
  pointer corrected to the `forms/` package-marker twin.
- **Unchanged:** import list, `__all__` (still exactly the four public
  symbols), no production code path changes.
- **Kept separate:** dual root + subpackage facade; leaf-only internals;
  filters/orders Decision-11 helpers; deferred sets/resolvers work.
- **Validation:** `uv run ruff format` + `uv run ruff check --fix` on the
  target (clean). Runtime identity re-checked for the four curated names.
  No permanent test added (docstring-only knowledge fix; existing export /
  identity pins already cover the surface). Full pytest not run (per
  assignment).
- **Changelog:** no — docstring accuracy only; no public API change.
- **Concurrent dirty paths:** left untouched. Plan checkbox not flipped.

Item-scoped source diff vs `ITEM_BASELINE`
`f6557d9c1eff1a6ea1a2a1ad3a352ea33ff22b4f` is the docstring rewrite only.
Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced the target as the curated `django_strawberry_framework.mutations`
consumer surface only: four eager re-exports + `__all__`, no class bodies,
registries, or bind/resolver/permission policy. Finalizer reaches
`mutations.sets.bind_mutations` via dotted leaf import; forms / rest_framework /
auth / package tests reach leaf modules the same way. Dual root + subpackage
facade confirmed: root `__init__` re-exports the same four names; runtime
`is` identity holds root ≡ `mutations` ≡ leaf for all four; internals
(`DenyAll`, `iter_mutations`, `register_mutation`, `bind_mutations`,
`NON_FIELD_ERROR_KEY`) stay off the package object until leaf import.

**Docstring consolidation challenged and accepted.** Five sibling modules on
disk (`fields`, `inputs`, `permissions`, `resolvers`, `sets`); baseline text
said "four-module" while listing five bullets including Decision 15
`permissions.py`. That is one overview encoding the module inventory twice
with incompatible counts — a real in-file knowledge divergence, not a line-count
tidy. Post-fix text is "five-module", names Decision 4's quartet + Decision 15,
drops slice-era closing narrative, and correctly separates the four-symbol
export claim from the five-module layout. TREE already lists all five; standing
docs were not a second competing overview owned by this file.

**Export surface unchanged.** Item-scoped diff is docstring-only. AST compare
vs `ITEM_BASELINE`: import list and `__all__` tuple identical
(`DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`).

**Rejected candidates re-challenged — all stand:**

1. Shared eager-re-export helper — packaging idiom across markers; different
   curated lists and change axes; a helper would obscure 1:1 import/`__all__`
   ownership.
2. Collapse root + `mutations` dual path — distinct product contracts (always-on
   root vs namespace-qualified); identity pins forbid divergent objects.
3. Widen `__all__` with leaf internals — Decision 5 / `tests/base/test_init.py`
   freeze the four-symbol consumer surface; submodule imports remain for
   white-box / framework paths.
4. Decision-11-style `mutation_input_type` — mutations materialize via Meta +
   finalizer bind; no helper ledger on this marker.
5. Missing package-path `DjangoMutationField` `is` pin — test-coverage nicety
   for `tests/mutations/test_fields.py`, not production duplication here
   (root `__all__` already names it; runtime identity already holds).
6. Metaclass factory (landed at `mutations/sets`) / plain-form fold (still
   deferred to `resolvers`) — owned by those modules, not this marker.

**Missed consolidations owned by this file:** none. Cross-reference to
`forms/__init__.py` as the closer packaging twin is accurate (filters/orders
carry Decision-11 helpers). Spec-036's historical four-module Decision 4 text
is design history, not a live second inventory this marker must rewrite.
`auth.mutations` is a different opt-in surface.

**Blockers:** none. Status → verified; plan item checked.
