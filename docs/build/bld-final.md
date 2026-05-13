# Build: Final test-run gate

Spec reference: `docs/spec-relay_interfaces.md`
Status: final-accepted

## Plan (Worker 1)

Run `uv run pytest` and verify the suite passes; coverage line-by-line is out of scope at this gate (CI's `pyproject.toml [tool.coverage.report] fail_under = 100` and the maintainer own that, not this gate).

## Test-run report (Worker 1)

- Command: `uv run pytest`
- Result: **516 passed, 1 skipped, 3 warnings in 23.83s**.
- The single skip is the pre-existing env-tied `FAKESHOP_SHARDED` skip (carried across the entire `0.0.5` build per Worker 1 memory). The two Slice-1-era Relay placeholder skips were both unskipped earlier in the cycle (Slice 4 lifted the composite-pk placeholder; Slice 5's promotion + bypass deletion unlocked the end-to-end paths the rest of the placeholders had been waiting on). No Relay-related skip remains.
- The three warnings are pre-existing and not introduced by this build: one `UserWarning` about `DATABASES` override inside `examples/fakeshop/tests/test_commands.py::test_seed_shards_command_runs_when_shard_alias_present` (sharded-mode test), and two `RuntimeWarning` entries about Django re-registering a `_owner` model inside `tests/types/test_converters.py`. Both predate the `relay_interfaces` build.
- CHANGELOG sanity-check: **Y**. The `[0.0.5]` section at `CHANGELOG.md:10-20` reads coherently — `### Added` lists the five user-visible behaviors (Relay Node interface acceptance via `Meta.interfaces`, the four resolver defaults with consumer-override preservation via `__func__` identity, `id: int!` suppression with `id: GlobalID!` substitution, unconditional `is_type_of` injection with consumer preservation, the composite-pk `ConfigurationError`, and both sync/async paths for `_resolve_node_default` / `_resolve_nodes_default`) and `### Changed` carries the verbatim canonical promotion line `Meta.interfaces promoted from DEFERRED_META_KEYS to ALLOWED_META_KEYS.` The four Slice-5 canonical phrasings (composite-pk constraint sentence, `is_type_of` scope sentence, resolver-list literal order, promotion line) landed inside the changelog entry verbatim per the integration pass's verification.
- Failures: **None.**

## Final verification (Worker 1)

- pytest passed: **Y** (516 passed, 1 skipped).
- CHANGELOG sanity: **Y**.

### Summary

The `relay_interfaces` / `0.0.5` build closes cleanly. Five spec slices shipped — Slice 1 added the `_validate_interfaces` Meta-shape validator and threaded the normalized `interfaces` tuple into `DjangoTypeDefinition` storage; Slice 2 added unconditional `is_type_of` injection (via `install_is_type_of`) with `__dict__`-membership consumer preservation; Slice 3 added tuple-membership `id` annotation suppression inside `_build_annotations` when `relay.Node in interfaces`; Slice 4 added Phase 2.5 of `finalize_django_types()`, wiring `apply_interfaces` (`__bases__` mutation), the composite-pk `ConfigurationError` gate, and `install_relay_node_resolvers` with `__func__`-identity override preservation across the four `resolve_id_attr` / `resolve_id` / `resolve_node` / `resolve_nodes` defaults; Slice 5 promoted `"interfaces"` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`, deleted the `tests/_relay_bypass.py` scaffolding plus the superseded `docs/spec-relay_interfaces-3.md`, refreshed the five canonical docs (`docs/FEATURES.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`), and bumped the version triplet to `0.0.5`. The cross-slice integration pass found no DRY drift, no canonical-phrasing drift, and confirmed the four-discriminator architecture (`_validate_interfaces` at class-creation, `__dict__` membership for `is_type_of`, tuple membership for `id` suppression, `issubclass` MRO + `__func__` identity for the four Relay resolver defaults) remained structurally split — no discriminator collapsed into a generic helper, matching upstream `strawberry-django`'s own posture. `__init__.py`'s `__all__` is unchanged at the six pinned names (Definition of done item 11). The full sweep across `tests/`, `examples/fakeshop/tests/`, and `examples/fakeshop/test_query/` runs in ~24 seconds with 516 passing tests, including the five intentional `pytest-asyncio` async tests under `tests/types/test_relay_interfaces.py` (no accidental async test elsewhere) and the live `/graphql/` HTTP round-trip for `GenreType` via the library acceptance suite.

### Spec changes made (Worker 1 only)

No spec edits. Slice 4's prior Decision 3 clarifications (`docs/spec-relay_interfaces.md:313-315`) and Slice 5's prior status-line trim (`docs/spec-relay_interfaces.md:3`) remain the only spec changes for this build; the final test-run gate surfaced no further reconciliation needs.

### Final status

`final-accepted`
