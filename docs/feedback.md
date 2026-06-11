# Review - spec-032 Full Relay implementation (post-build code review)

Reviewed the committed implementation (`3b8173dc..HEAD`, ~3,600 insertions) against
`docs/spec-032-full_relay-0_0_9.md` Revision 7 and the prior review passes: the new
`relay.py` / `testing/relay.py` modules in full, the diffs to `types/base.py`,
`types/finalizer.py`, `types/definition.py`, `connection.py`, `registry.py`, both
`__init__.py`s, the fakeshop activation, and the five test surfaces. Worker-local
validation run: `ruff format --check` / `ruff check` clean,
`check_spec_glossary.py` -> `OK: 40 terms`; no pytest per `AGENTS.md`.

Verdict: this is a high-quality build. Every contract from the three review passes
landed verbatim and is cited in-source: the `strawberry.ID` raw-string arguments
(`relay.py` notes the `convert_argument` interception that made `relay.GlobalID`
annotations unusable - Revision 7 P1), the narrowly-scoped `GLOBALID_INVALID`
boundary with the discriminating `SyncMisuseError`-is-not-`GLOBALID_INVALID` test,
the uncoercible-pk -> `null` contract with query-count pins, the whole-field
malformed-batch failure, the per-call `in_async_context()` gathering coroutine, the
two-stage `relation_shapes` validation, the camel-surface collision guard, the
no-Node-types ledger with `registry.clear()` co-clear, and Decision-13 compliance
(version untouched at `0.0.8`; CHANGELOG bullets under `[Unreleased]` only).

The build also surfaced and correctly fixed three bugs of its own, each pinned by a
regression test: (1) handing the schema the generic alias
`DjangoConnection[target]` lost the package's `resolve_connection` override at
Strawberry's generic specialization - meaning the shipped `first`+`last` guard
**never ran through-schema for non-`totalCount` connections** (a latent spec-030
bug; fixed by always generating concrete `<TypeName>Connection` classes with the
parent's SDL description preserved); (2) a partial-finalize rerun re-attached the
Phase-2 list resolver for a `"connection"`-shaped relation, which the marker-based
re-suppression now handles; (3) the async gatherer awaited `resolve_nodes`
unconditionally, breaking valid synchronous consumer overrides
(`TypeError: 'list' object can't be awaited`) - now awaitable-or-value. Findings
below are graded against that baseline.

## Findings

### P2 - `_coerce_pk_or_none` coerces against `model._meta.pk`, but resolution filters on `resolve_id_attr()` - breaking supported custom `relay.NodeID[...]` types

`relay.py::_coerce_pk_or_none` runs `_model_for(resolved_type)._meta.pk.to_python(node_id)`
unconditionally. But the shipped resolution path it feeds keys on a *different*
field: `_resolve_node_default` / `_resolve_nodes_default` derive
`id_attr = cls.resolve_id_attr()` and filter `{id_attr: <coerced>}` /
`{id_attr}__in`. For the default (`"pk"`) the two coincide and everything here is
correct. They diverge exactly where the package already promises support:

- `types/relay.py::_resolve_id_attr_default` explicitly honors a consumer
  `id: relay.NodeID[...]` annotation ("a consumer NodeID annotation on the class
  wins"), and `_resolve_id_default` emits that attribute's value as the id slot.
- `_check_composite_pk_for_relay_node`'s error message *instructs* consumers to
  "declare an explicit `id: relay.NodeID[...]` annotation" as the composite-pk
  escape hatch - the one path where `_meta.pk` is a `CompositePrimaryKey` and
  single-column `to_python` semantics do not exist at all.

Concrete failures for a type with `code: relay.NodeID[str]` over an integer-pk
model: `node(id:)` for code `"abc"` coerces against the int pk -> `ValidationError`
-> spurious `null` for a row that exists; code `"007"` coerces to int `7`, the
default then filters `code=7` -> Django stringifies to `"7"` != `"007"` -> wrong
miss. On a composite-pk model with the documented NodeID escape, every root
refetch is broken. None of the three new test files contains a custom-NodeID case
(grep: zero `NodeID` hits), so the gap is invisible to CI.

**Fix:** derive the coercion field from the same source the resolution uses -
`id_attr = resolved_type.resolve_id_attr()`; map `"pk"` to the concrete
`model._meta.pk`, otherwise `model._meta.get_field(id_attr)`; if the NodeID attr
does not name a concrete model field, skip coercion and pass the raw string (the
pre-032 default behavior, which Django handles for non-pk columns). Add
`test_node_custom_node_id_attr_resolves` / `..._uncoercible_returns_null` package
tests. Severity P2 not P1 because the default path (every shipped and fakeshop
type) is correct; the broken paths are consumer-reachable but unexercised.

### P3 - `_interleave`'s positional 1:1 contract on consumer `resolve_nodes` overrides is load-bearing but undocumented

`relay.py::_interleave` maps each input position to
`per_type_results[type][within-group index]` - it requires every `resolve_nodes`
return to be input-ordered, exactly `len(node_ids)` long, and `None`-padded for
missing ids. The framework default guarantees that (`_resolve_nodes_default`'s
documented 1:1 contract via `_order_nodes`), and the gatherer now correctly
handles sync-or-async returns. But `DjangoNodesField` deliberately calls the
*classmethod* to preserve consumer overrides, and an override written the obvious
way (`return cls.get_queryset(...).filter(pk__in=node_ids)`) violates all three
assumptions: unordered rows, missing ids shrink the list, and duplicates produce
an `IndexError` (two positions index 0 and 1 of a one-row result). Strawberry's
native batch resolver makes the same positional assumption, so the contract is
ecosystem-consistent - but nothing consumer-facing states it.

**Fix (documentation-first):** one paragraph in the `DjangoNodesField` docstring
pinning the override contract ("input-ordered, 1:1 with `node_ids`, `None` for
missing - the `_resolve_nodes_default` shape"), plus optionally a cheap defensive
`len(result) == len(pks)` check that raises a `ConfigurationError` naming the
offending type instead of a bare `IndexError` / silently wrong rows.

### P3 - Synthesized relation connections have no async escape for async-`get_queryset` targets

`connection.py::_build_relation_connection_resolver` is sync-pipeline-only by
design (a lazy queryset works under both execution modes). The documented escape
for an async `get_queryset` hook on a *root* connection is "supply an `async def`
`resolver=`" (`_build_connection_resolver`'s docstring) - but a synthesized
relation connection has no `resolver=` seam, so a Relay target whose
`get_queryset` is `async def` makes its synthesized `<field>Connection` raise
`SyncMisuseError` on every query, with `relation_shapes={"<field>": "list"}` as
the only recourse. That is a defensible 0.0.9 posture (the fail-loud
`SyncMisuseError` contract is inherited, not new), but it is currently recorded
nowhere a consumer would look. **Fix:** a sentence in the
`_build_relation_connection_resolver` docstring and the `Meta.relation_shapes`
GLOSSARY entry; an async pipeline seam for synthesized connections can ride the
`033` connection-pipeline work if demand appears.

## Verified sound (checked, no action)

- **Slice 1 diagnostics:** the named-helper table matches the spec's six messages;
  identity matching (`entry is helper`) and placement *before* the non-class
  branch are both load-bearing and correctly reasoned - `relay.NodeID` is an
  `Annotated` alias, not a class, so a later placement would die unnamed in the
  generic rejection. All eight messages pinned in `tests/types/test_base.py`.
- **Ledger lifecycle:** plain (non-try/except) import in the finalizer with the
  contract-check-must-not-skip rationale; `registry.clear()` co-clear in the
  established cycle-safe shape; the exact card message string.
- **`relation_shapes` validation:** stage-1/stage-2 split mirrors the
  `nullable_overrides` precedent; unhashable-value guard before set membership;
  sorted deterministic messages; `dict(value)` defensive copy; consumer-authored
  raise at creation plus the implicit-default skip at synthesis - both halves of
  Revision 3 P2 intact.
- **Synthesis:** eligibility via the single-source `FieldMeta.is_many_side`
  classifier; explicit-vs-implicit non-Node-target split; collision guard on both
  Python and default-camel-cased surfaces (recomputed per relation so earlier
  synthesized siblings participate); list-form suppression before Phase 3;
  ordering before `_bind_filtersets` so synthesized sidecar registrations are
  orphan-validated in the same finalize.
- **Decision-13 / docs:** version files untouched; `[Unreleased]` carries the
  three `### Added` bullets; `DjangoNodesField` / `Meta.relation_shapes` GLOSSARY
  entries exist; `test_init.py` export tuple updated.
- **Fakeshop activation:** BookType promotion + `circulation_status="repair"`
  hook (enum constant, staff bypass, hoisted `_user_is_staff` deduplicating three
  copies); the full live matrix is present including
  `test_has_next_page_correct_when_edges_unrequested`,
  `test_node_uncoercible_pk_live`, the loans graceful-degradation proof, and the
  hidden-row staff/anon split.
- **Uncapped `nodes(ids:)`** is now a recorded decision (spec Edge cases + Risks),
  matching the implementation's behavior - no code action needed.

## Checks run

- `uv run ruff format --check .` -> 241 files already formatted;
  `uv run ruff check .` -> all checks passed.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md`
  -> `OK: 40 terms`.
- Source reads: `relay.py` / `testing/relay.py` in full; `types/base.py`,
  `types/finalizer.py`, `types/definition.py`, `connection.py`, `registry.py`,
  package/testing `__init__.py` diffs; `types/relay.py` resolution internals
  (`_resolve_id_attr_default`, `_order_nodes`, `_apply_node_filter`,
  `_resolve_node(s)_default`); fakeshop schema diff; test-name surveys plus
  targeted reads of the async and malformed-id suites.
- No pytest run per repo instructions (`AGENTS.md` "Do not run pytest after
  edits"); test execution is CI-owned.
