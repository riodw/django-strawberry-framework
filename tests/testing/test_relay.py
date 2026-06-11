"""Staged test home for the public ``testing.relay`` helpers (spec-032 Slice 5).

Mirrors ``django_strawberry_framework/testing/relay.py`` per the
``docs/TREE.md`` one-to-one rule (``docs/spec-032-full_relay-0_0_9.md``
Decision 11 - no card conflict for this pair). Staged list below is removed
by the change that ships Slice 5.
"""

# TODO(spec-032-full_relay-0_0_9 Slice 5): Helper coverage (Decision 10).
#   test_global_id_for_model_strategy / ..._type_strategy /
#   ..._type_plus_model_strategy
#     the helper's output equals the live emitted id (cross-checked against
#     a schema execution).
#   test_global_id_for_callable_or_custom_raises
#     "callable" / "custom" strategies need a live (root, info) pair the
#     helper does not have -> ConfigurationError.
#   test_global_id_for_unfinalized_raises / test_global_id_for_non_node_raises
#     the finalize-first remediation; non-Relay-Node inputs raise.
#   test_public_decode_round_trip_primary_and_type_name
#     decode_global_id(global_id_for(T, pk)) == (T, str(pk)) ONLY for
#     lone/primary model-label types and type-strategy payloads (Rev 2 P2).
#   test_secondary_model_label_emitter_decodes_to_primary
#     global_id_for(SecondaryType, pk) mints the model-label payload the
#     secondary emits; decode_global_id resolves it to (primary_type,
#     str(pk)) via registry.get(model) - the documented asymmetry.
