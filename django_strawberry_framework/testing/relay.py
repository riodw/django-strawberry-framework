"""Public Relay test helpers - ``global_id_for`` / ``decode_global_id``.

Staged home for ``WIP-ALPHA-032-0.0.9`` Slice 5 (``docs/spec-032-full_relay-0_0_9.md``
Decision 10): the two helpers consumer test suites use to mint and assert the
durable ``GlobalID``s the ``0.0.9`` strategy system emits. Lives under
``testing/`` (not the package root) because the audience is consumer *test
suites*; the export was withheld in ``0.0.9``'s spec-031 cycle until this
card shipped the consumer (the tested-usage promotion discipline).

Statement-free until Slice 5 lands (``fail_under = 100``); the Slice-5 change
replaces the staged pseudocode and removes the anchors per the ``AGENTS.md``
design-doc anchor discipline.
"""

# TODO(spec-032-full_relay-0_0_9 Slice 5): Strategy-aware id mint.
#   def global_id_for(type_cls, id) -> str:
#       definition = type_cls.__django_strawberry_definition__  # noqa: ERA001
#       # missing / not finalized -> ConfigurationError with the
#       # finalize-first remediation; non-Relay-Node -> ConfigurationError
#       strategy = definition.effective_globalid_strategy  # noqa: ERA001
#       if strategy in {"model", "type+model"}:
#           payload = definition.model._meta.label_lower  # noqa: ERA001
#       elif strategy == "type":  # noqa: ERA001
#           payload = definition.graphql_type_name  # noqa: ERA001
#       else:  # "callable" / "custom"  # noqa: ERA001
#           raise ConfigurationError(...)  # encode needs a live root/info  # noqa: ERA001
#       return str(relay.GlobalID(type_name=payload, node_id=str(id)))  # noqa: ERA001
# Asymmetry contract (Decision 10 / Revision 2 P2): a SECONDARY model-label
# emitter mints the payload it genuinely emits, while decode routes that same
# payload to the model's PRIMARY via ``registry.get(model)`` - round-trip
# identity holds only for lone/primary model-label types and for
# ``type``-strategy payloads. Documented, not "fixed": it is exactly the
# routing a live ``node(id:)`` performs on the same id.

# TODO(spec-032-full_relay-0_0_9 Slice 5): Public decode re-export.
#   from django_strawberry_framework.types.relay import decode_global_id  # noqa: ERA001
# Same uniform-ConfigurationError contract and ``(target_type, node_id)``
# return; the internal signature is already consumer-shaped.
