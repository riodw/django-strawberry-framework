# DRY review: `django_strawberry_framework/filters/inputs.py`

Status: verified

## System trace

Owns filter-input materialization for spec-027 Decision 9: lookup vocabulary
(`LOOKUP_PREFIXES` / `LOOKUP_NAME_MAP` / `_LOGIC_KEYS`), the filter-instance →
Strawberry annotation converter pair (`convert_filter_to_input_annotation` /
`normalize_input_value`), per-filterset field + logic builders
(`_build_input_fields` / `_build_logic_fields`), range / GlobalID / enum value
helpers, and the family ledger wrappers (`materialize_input_class` /
`clear_filter_input_namespace`).

Shared generated-input mechanics already live in
`utils/inputs.py` (`GeneratedInputFieldSpec`, `build_strawberry_input_class`,
`emit_set_input_field_triples`, `materialize_generated_input_class`,
`clear_generated_input_namespace`, `optional_field_kwargs`) and
`utils/input_values.py` (`iter_active_fields` for `FilterSet._normalize_input`).
This module keeps filter-domain semantics and re-exports the substrate under
spec-named aliases (`FieldSpec` / `build_input_class` / `_camel_case` /
`_iter_filterset_subclasses`).

Callers: `filters/factories.py` (BFS build), `filters/sets.py` (normalize +
logic wire keys), `filters/__init__.py` (`filter_input_type` / module path),
`registry.clear` via `register_subsystem_clear`. Live GraphQL coverage for
lookups, logic (`and` / `or` / `not`), GlobalID, and choice enums already
exists under `examples/fakeshop/test_query/` (library / kanban / products /
scalars filter APIs). Sibling `orders/inputs.py` mirrors the family wrapper
shape; shared mechanics are already single-sited — remaining order-side
differences (fixed `Ordering | None` leaves, no operator bag / logic keys /
`HIDE_FLAT_FILTERS`) are intentional and belong to folder / project passes.

## Verification

- Baseline diff for the target at `ITEM_BASELINE` was empty; work started from
  HEAD.
- Compared `orders/inputs.py`, `utils/inputs.py`, `utils/write_values.py`,
  `forms/converter.py` (`_SCALAR_FORM_FIELDS`), `sets_mixins.py`
  (`pascal_case_or_raise`), and `FilterSet._normalize_input`.
- Confirmed `_LOGIC_KEYS` was documented as the single name-pairing source and
  consumed by `sets.py`, but `_build_logic_fields` re-spelled the three
  `(python_attr, wire_name)` pairs — a real drift axis inside this file's
  ownership.
- Disproved consolidating `_scalar_from_form_field` with forms'
  `_SCALAR_FORM_FIELDS`: NullBoolean → `bool` here (outer `| None` for
  optionality) vs `bool | None` on the write form table; filters omit
  `JSONField` / `ChoiceField` rows and use an isinstance chain ordered for
  django-filter form subclasses. Different contracts.
- Disproved folding `_unwrap_enum_member` into `write_values.raw_choice_value`:
  identical one-liner, but `write_values` is explicitly write-flavor scoped;
  promoting a shared owner belongs in a neutral util / project pass, not by
  making filter normalize import the write path.
- Disproved promoting `_encode_global_id_input` toward write GlobalID helpers:
  filters re-encode to wire form so `GlobalIDFilter` can validate `type_name`;
  write paths decode. Opposite direction.
- Disproved further collapsing the orders/filters family wrappers
  (`INPUTS_MODULE_PATH`, `_input_type_name_for`, thin materialize/clear):
  substrate already shared; remaining mirror is Decision-9 per-subsystem
  namespace ownership. Folder / project.
- Path-walk similarity (`_model_field_for_filter` vs `utils/relations` /
  connection path walkers) is structural Django `_meta.get_field` iteration
  with different return contracts (terminal field vs fan-out / relation kind).

## Opportunities

### 1. `_build_logic_fields` must derive names from `_LOGIC_KEYS`

- **Repeated responsibility:** Python-attr ↔ GraphQL wire-name pairing for
  `and` / `or` / `not`.
- **Sites:** `_LOGIC_KEYS` (module constant; imported by `filters/sets.py`) and
  the hardcoded triples formerly inside `_build_logic_fields`.
- **Evidence:** Module comment claimed local consumption via
  `_build_logic_fields`, but the builder re-listed the three pairs. Adding a
  logic key to `_LOGIC_KEYS` would teach the normalizer a wire key the
  generated input never emitted.
- **Owner:** `filters/inputs.py` (`_LOGIC_KEYS` + `_build_logic_fields`).
- **Consolidation:** Iterate `_LOGIC_KEYS`; keep list-vs-scalar arity as the
  only local divergence (`and_` / `or_` → `list[self_ref]`, `not_` →
  `self_ref`); emit kwargs via `optional_field_kwargs`.
- **Proof:** `tests/filters/test_inputs.py::test_build_logic_fields_tracks_logic_keys`
  plus existing H2 / keyword-name unit tests; live `and` / `or` / `not`
  queries already cover wire behavior.
- **Risks / non-goals:** Do not encode order-side absence of logic keys here;
  do not change django-filter wire keys.

## Judgment

Prior 0.0.9 substrate extraction already removed the large cross-family
duplication. The remaining load-bearing fix inside this file's ownership is
making `_build_logic_fields` obey `_LOGIC_KEYS`. Other lookalikes are
intentional domain boundaries or project-scope owner questions.

## Implementation (Worker 1)

- **Owner:** `filters/inputs.py::_build_logic_fields` over `_LOGIC_KEYS`.
- **Migrated:** hardcoded `and_` / `or_` / `not_` triples → comprehension over
  `_LOGIC_KEYS` + `optional_field_kwargs`; comment on `_LOGIC_KEYS` updated.
- **Tests:** `test_build_logic_fields_tracks_logic_keys` in
  `tests/filters/test_inputs.py`.
- **Kept separate:** form-field scalar table, enum unwrap vs write path,
  GlobalID encode vs decode, orders family wrappers, path walkers.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .`.
- **Changelog:** no — internal DRY; public filter input surface unchanged.

## Independent verification (Worker 2)

Re-traced filter-input ownership and the logic-key contract end to end:
`_LOGIC_KEYS` → `_build_logic_fields` (emission) → `factories.py` field triples →
`sets.py` (`_LOGIC_WIRE_BY_PYTHON_ATTR`, `_LOGIC_PYTHON_ATTRS`, async branch walk,
`_normalize_input`). Confirmed the pre-fix drift axis was real: the module
comment already named `_LOGIC_KEYS` as the single pairing source and `sets.py`
imported it, while `_build_logic_fields` re-spelled the three
`(python_attr, wire_name)` triples. Adding a key to `_LOGIC_KEYS` alone would
teach the normalizer a wire key the generated input never emitted.

**Migration + proof:** Scoped diff matches the artifact. Builder iterates
`_LOGIC_KEYS`, routes kwargs through `optional_field_kwargs`, and keeps
list-vs-scalar arity as the only local divergence (`list_attrs`). Scratch check
confirmed emitted `(attr, name)` pairs equal `list(_LOGIC_KEYS)` and kwargs match
`optional_field_kwargs`. `test_build_logic_fields_tracks_logic_keys` pins that
parity; package-tier placement is correct for a private helper. Live `and` /
`or` / `not` wire behavior remains covered under `examples/fakeshop/test_query/`
(kanban + library).

**Rejected candidates (disposed):**

- **Orders family wrappers** — substrate already shared via `utils/inputs.py`;
  remaining mirror is Decision-9 per-subsystem namespace ownership (no logic
  keys / operator bag on orders). Folder / project, not this file's fix.
- **Form scalars** — `_scalar_from_form_field` vs forms `_SCALAR_FORM_FIELDS`:
  NullBoolean → bare `bool` here (outer `| None` for optionality) vs
  `bool | None` on the write table; filters omit `JSONField` / `ChoiceField`
  and use an isinstance chain ordered for django-filter form subclasses.
  Different contracts.
- **Enum unwrap** — `_unwrap_enum_member` and `write_values.raw_choice_value`
  are the same one-liner, but write-flavor scoping is intentional; a neutral
  util belongs in a project pass, not by making filter normalize import the
  write path.
- **GlobalID encode vs decode** — filters re-encode to wire form for
  `GlobalIDFilter` type_name validation; write paths decode. Opposite
  direction; correctly kept separate.
- **Arity residual (`list_attrs` / `sets.py` `wire_key == "not"`)** — not the
  claimed shared responsibility. Name pairing was the load-bearing drift axis;
  list-vs-scalar shape is a separate, intentionally local rule already
  documented in the builder. Folding arity into `_LOGIC_KEYS` is out of scope
  for this item and does not reopen the finding.

**Missed opportunities:** None inside this file's ownership. No leftover
hardcoded logic-name triples in `inputs.py`. No blockers.

**Outcome:** verified. Plan item checked.
