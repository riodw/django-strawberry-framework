# DRY review: `django_strawberry_framework/management/commands/inspect_django_type.py`

Status: verified

## System trace

The target owns `manage.py inspect_django_type`: a diagnostic CLI that resolves a
finalized `DjangoType` (dotted path or bare registry / SDL / Python name) and
prints a per-selected-field table of Django field type, GraphQL type,
nullability, and which converter / override row produced it. It reads the
post-finalize surface (`origin.__annotations__`,
`origin.__strawberry_definition__`, definition override ledgers,
`relation_connections`) rather than re-running synthesis.

Symbols (module + `Command`):

- `Command` / `add_arguments` / `handle` — `--schema` import, naming config,
  resolve, finalize gate, table print.
- `_resolve_type` / `_resolve_bare_name` — dotted `import_string` vs unique
  registry match on SDL name + `__name__`.
- `_print_table` / `_resolve_row` — selection-order rows; dispatch order:
  Relay-suppressed pk → consumer-authored → relation → scalar.
- `_is_suppressed_relay_pk` — pk row as `GlobalID!` / `relay.Node id` when the
  type is Relay-Node-shaped (must match `_build_annotations` suppression).
- `_relation_row` / `_suppressed_connection_name` /
  `_connection_only_relation_row` — auto relations, including
  `relation_shapes="connection"` (list annotation popped).
- `_scalar_row` / `_matched_scalar_key` — annotation render + converter label
  (`convert_field_output`, choice enum, or `SCALAR_MAP[<MRO ancestor>]`).
- `_consumer_authored_row` / `_consumer_nullable` / `_consumer_converter_label` —
  Strawberry field metadata + four-corner override labels; `UNRESOLVED` →
  `CommandError`.
- `_GRAPHQL_SCALAR_NAMES` / `_scalar_name` / `_render_annotation` /
  `_render_strawberry_type` / `_sdl_type_name` / `_yes_no` /
  `_annotation_is_optional` / `_RELATION_KIND_LABELS` — presentation helpers
  for cold-path and schema-backed naming.

Dependencies already owned elsewhere:

- `_imports.import_module_symbol_or_command_error` /
  `import_string_or_command_error` — shared with `export_schema`.
- `scalars._PACKAGE_SCALAR_MAP` — cold-path package scalar names (BigInt),
  already merged into `_GRAPHQL_SCALAR_NAMES` (preserve; do not hardcode).
- `types.base.DjangoType` + `types.base._is_relay_shaped` — type gate +
  Relay-shape predicate (same inputs `_build_annotations` uses for pk
  suppression).
- `types.converters.SCALAR_MAP` / `_field_output_type_for` — converter
  attribution; shared MRO walks stay in converters for value lookup.
- `registry` — bare-name resolution / finalized definitions.

Callers / registration:

- Django discovers the command via
  `django_strawberry_framework.management.commands.inspect_django_type`. No
  package production import of `Command`; consumers use `manage.py` /
  `call_command`.

Proof / placement (AGENTS.md tiers):

- Package: `tests/management/test_inspect_django_type.py` (CommandError paths,
  helpers, connection-only shape, unresolved forward ref, direct-inheritance
  Relay pk).
- Project: `examples/fakeshop/tests/test_inspect_django_type.py` (live schema
  types, Meta.interfaces Relay pk, bare names, `--schema` cold path).
- Not `test_query/` — management command, not live GraphQL HTTP.

Baseline
`git diff 2c739c9450dc0ad1772a153f2fb8718024e255fd -- …/inspect_django_type.py`
was empty at review start; concurrent dirty paths elsewhere left untouched.

## Verification

Searches / comparisons:

- Inline Relay predicate: only this file and
  `types/base.py::_is_relay_shaped` encode
  `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`.
  `list_field.py` already imports the shared helper.
- `types/relay.py::implements_relay_node` — MRO-only post-injection
  `issubclass(type_cls, relay.Node)`. Distinct lifecycle owner for finalizer /
  filters / mutations; does **not** replace `_is_relay_shaped` for the
  synthesis-time / Meta.interfaces + direct-inheritance contract the inspect
  pk row must mirror.
- `_matched_scalar_key` vs `converters.scalar_for_field` — same MRO walk over
  `SCALAR_MAP`, different contracts (soft class-name label vs scalar value /
  `ConfigurationError`). Diagnostic naming stays local.
- `_annotation_is_optional` / `_render_*` / `_RELATION_KIND_LABELS` — CLI
  presentation only; no second production owner.
- `_GRAPHQL_SCALAR_NAMES` + `_PACKAGE_SCALAR_MAP` — already single-sourced for
  package scalars; built-in GraphQL names are fixed SDL constants.
- Sibling `export_schema` — shared import helpers only; no Schema-instance
  guard shared (inspect imports `--schema` for side effects + `.config`).
- `_make_test_module` duplication with `test_export_schema` — intentional
  independent CLI fixtures (rejected in export_schema artifact; still holds).

Rejected / deferred:

1. **Use `implements_relay_node` instead of `_is_relay_shaped`.** Rejected:
   different contract (post-base-injection MRO vs declared interfaces ∪
   inheritance). Inspect must stay aligned with `_build_annotations`
   suppression, which calls `_is_relay_shaped`.
2. **Hoist `_matched_scalar_key` into `converters`.** Rejected: soft diagnostic
   fallback vs hard lookup failure; would couple CLI labeling into the
   conversion owner without a second production consumer.
3. **Share Schema-resolve helper with `export_schema`.** Rejected: inspect must
   not require `isinstance(..., Schema)`; different post-import contracts.
4. **Extract `_RELATION_KIND_LABELS` / render helpers to a shared module.**
   Deferred: one consumer; presentation, not policy. Revisit only if a second
   diagnostic surface needs the same labels.
5. **Reverse BigInt cold-path naming off `_PACKAGE_SCALAR_MAP`.** Rejected
   (preserve prior scalars DRY): hardcoded `"BigInt"` would drift from
   `strawberry_config()`.

## Opportunities

### 1. Consume shared `_is_relay_shaped` for suppressed Relay pk rows

- **Repeated responsibility:** Whether a `DjangoType` is Relay-Node-shaped
  (`Meta.interfaces` entry subclassing `relay.Node`, or direct
  `relay.Node` inheritance) — the gate that suppresses the synthesized pk
  annotation and must drive the inspect `GlobalID!` row.
- **Sites:** Owner `types/base.py::_is_relay_shaped` (used by
  `_validate_meta` / `_build_annotations` / `list_field`); duplicate inline
  boolean in `Command._is_suppressed_relay_pk`.
- **Evidence:** Byte-equivalent expression on the same inputs
  (`definition.origin`, `definition.interfaces`). Both change when Relay-shape
  spelling rules change (e.g. custom `Node` interface subclasses).
- **Owner:** `types/base.py::_is_relay_shaped`.
- **Consolidation:** Import and call
  `_is_relay_shaped(definition.origin, definition.interfaces)`; drop local
  `strawberry.relay` import used only for the re-derivation.
- **Proof:** Existing fakeshop `BookType` (`Meta.interfaces`) + new package test
  `test_inspect_direct_relay_node_inheritance_suppresses_pk_row` (direct
  inheritance arm).
- **Risks / non-goals:** Do not switch to `implements_relay_node`; do not move
  CLI presentation helpers into `types/base.py`.

## Judgment

One real duplication: the Relay-Node-shape predicate. Everything else in this
file is either already delegated to shared owners (`_imports`,
`_PACKAGE_SCALAR_MAP`, converters MRO helpers) or CLI-only presentation that
should not invent a second policy module. Consolidate the predicate at
`_is_relay_shaped`; leave diagnostic rendering local.

## Implementation (Worker 1)

- **Owner chosen:** `types/base.py::_is_relay_shaped` (existing).
- **Migrated:**
  `management/commands/inspect_django_type.py::Command._is_suppressed_relay_pk`
  now calls `_is_relay_shaped`; removed unused `from strawberry import relay`.
- **Tests:**
  `tests/management/test_inspect_django_type.py::test_inspect_direct_relay_node_inheritance_suppresses_pk_row`
  (direct-inheritance arm; Meta.interfaces arm remains in
  `examples/fakeshop/tests/test_inspect_django_type.py`).
- **Kept separate:** `_matched_scalar_key`, render helpers, Schema import
  contract vs `export_schema`, `_PACKAGE_SCALAR_MAP` cold-path merge.
- **Validation:** `uv run ruff format .` and `uv run ruff check --fix .`
  (clean). No full pytest (per assignment).
- **Changelog:** not warranted (internal DRY; no public API change).
- **Concurrent work:** only this target + its package test + this artifact
  edited; other dirty paths untouched.
- **Ready for Worker 2.**

## Independent verification (Worker 2)

Re-traced `inspect_django_type` → `_is_suppressed_relay_pk` → synthesis pk
suppression in `types/base.py::_build_annotations` (`suppress_pk_annotation =
_is_relay_shaped(cls, interfaces)`), plus sibling consumers
(`list_field.py`), and the post-injection MRO owner
(`types/relay.py::implements_relay_node`). Item-scoped diff vs
`ITEM_BASELINE` is only the predicate migration + the direct-inheritance
package test; no unrelated absorption.

**Shared responsibility confirmed.** Baseline
`_is_suppressed_relay_pk` inlined
`any(issubclass(i, relay.Node) for i in definition.interfaces) or
issubclass(definition.origin, relay.Node)` — byte-equivalent to
`_is_relay_shaped(cls, interfaces)` on the same inputs
(`definition.origin`, `definition.interfaces`) that `_build_annotations`
uses when it suppresses the pk. Both sites must move when Relay-shape
spelling rules change (Meta interface, `CustomNode(relay.Node)`, direct
`class Foo(DjangoType, relay.Node)`). Owner is correctly
`types/base.py::_is_relay_shaped`.

**Migration complete.** Production search for the full predicate expression
finds only `types/base.py::_is_relay_shaped`. Inspect now calls that helper;
`from strawberry import relay` is gone from the command module. No leftover
inline duplicate, no stale local re-derivation.

**Rejected candidates re-challenged (all still hold):**

1. **`implements_relay_node`.** Distinct contract: MRO-only
   `issubclass(type_cls, relay.Node)` for post-`__bases__` injection
   (finalizer / filters / mutations). Inspect must mirror synthesis-time
   shape (`interfaces` ∪ inheritance), not assume Phase-2.5 injection
   already made MRO sufficient. Switching would couple the diagnostic row
   to finalizer side effects instead of the gate that actually suppressed
   the annotation.
2. **Hoist `_matched_scalar_key` into converters.** Same MRO walk as
   `scalar_for_field`, different contract: soft class-name label +
   concrete-name fallback vs scalar value / `ConfigurationError`. No second
   production consumer; CLI naming stays local.
3. **Share Schema-resolve with `export_schema`.** `export_schema` requires
   `isinstance(..., Schema)`; inspect imports `--schema` for side effects +
   `.config` duck-typing and must not require a Schema instance. Shared
   surface is already `_imports` only.
4. **Extract render / `_RELATION_KIND_LABELS`.** One diagnostic consumer;
   presentation, not policy.
5. **Hardcode BigInt.** `_GRAPHQL_SCALAR_NAMES` still merges
   `_PACKAGE_SCALAR_MAP` (`**{scalar: definition.name for ...}`); no
   hardcoded `"BigInt"` string. Prior scalars DRY preserved.

**Nearby non-duplicates (not missed opportunities for this target):**
`optimizer/walker.py` and `types/definition.py` use post-MRO
`issubclass(..., relay.Node)` for runtime / elision decisions — same
family as `implements_relay_node`, not the synthesis-shape predicate.
`_is_suppressed_relay_pk`'s remaining `field.name == pk.name` arm is
inspect dispatch after the shared shape check; inventing a second shared
helper for that would over-couple CLI row selection into `types/base`.

**Tests / placement.** Package tier
`tests/management/test_inspect_django_type.py::test_inspect_direct_relay_node_inheritance_suppresses_pk_row`
covers the direct-inheritance arm; fakeshop
`examples/fakeshop/tests/test_inspect_django_type.py` covers Meta.interfaces
(`BookType` / `GenreType`). Management-command surface — not live
`/graphql` — so package + project tiers are correct; `test_query/` would be
wrong.

**Outcome:** verified. No blockers. No production edits from Worker 2.
