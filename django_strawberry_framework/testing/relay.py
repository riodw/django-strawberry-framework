"""Public Relay test helpers - ``global_id_for`` / ``decode_global_id``.

The two helpers consumer test suites use to mint and assert the durable
``GlobalID``s the ``0.0.9`` strategy system emits (``docs/spec-032-full_relay-0_0_9.md``
Decision 10). Lives under ``testing/`` (not the package root) because the
audience is consumer *test suites*; the export was withheld in ``0.0.9``'s
spec-031 cycle until this card shipped the consumer (the tested-usage
promotion discipline).

- ``global_id_for(type_cls, id)`` mints the encoded ``GlobalID`` string a
  **finalized Relay-Node-shaped** type emits for a pk. The payload follows the
  type's finalize-stamped strategy: ``model`` / ``type+model`` emit the model
  label (``app_label.modelname``); ``type`` emits the ``graphql_type_name``;
  ``callable`` / ``custom`` raise ``ConfigurationError`` - those encoders run
  on a live ``root`` the helper does not have, so it cannot
  promise the emitted payload (a consumer with a custom encoder owns its own
  test helper). Finalize first: the strategy is stamped at finalization, so an
  unfinalized type (and a finalized non-Relay-Node type) raises too.
- ``decode_global_id(gid)`` is the public re-export of
  ``django_strawberry_framework.types.relay.decode_global_id`` - same uniform
  ``ConfigurationError`` contract and ``(target_type, node_id)`` return; the
  internal signature is already consumer-shaped.

Asymmetry contract (Decision 10 / Revision 2 P2): a SECONDARY model-label
emitter mints the payload it genuinely emits, while decode routes that same
payload to the model's PRIMARY via ``registry.get(model)`` - so
``decode_global_id(global_id_for(T, pk)) == (T, str(pk))`` holds only for
lone/primary model-label types and for ``type``-strategy payloads. Documented,
not "fixed": it is exactly the routing a live ``node(id:)`` performs on the
same id.

Importing this submodule (not ``testing/__init__``) is the public path; it
also keeps ``import django_strawberry_framework.testing`` light - the
``types``-package imports below are paid only by suites that use the helpers.
"""

from strawberry import relay

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.types.base import (
    _RELAY_NODE_GATE_INHERIT_TAIL,
    _RELAY_NODE_GATE_LEAD,
    STRING_GLOBALID_STRATEGIES,
)
from django_strawberry_framework.types.relay import decode_global_id, encode_typename

__all__ = ["decode_global_id", "global_id_for"]


def global_id_for(type_cls: type, id: object) -> str:  # noqa: A002
    """Return the encoded ``GlobalID`` string ``type_cls`` emits for ``id``.

    Reads the finalize-stamped ``effective_globalid_strategy`` (never the
    setting), so the helper is consistent-by-construction with live emission;
    raises ``ConfigurationError`` for non-``DjangoType`` inputs, unfinalized
    types, finalized non-Relay-Node types, and ``callable`` / ``custom``
    strategies (see the module docstring for the full contract).
    """
    definition = getattr(type_cls, "__django_strawberry_definition__", None)
    if definition is None:
        raise ConfigurationError(
            f"global_id_for: {type_cls!r} is not a registered DjangoType subclass; "
            "pass the DjangoType class whose emitted id you want to mint.",
        )
    if not definition.finalized:
        # Gate on ``finalized`` FIRST. The strategy stamp is written in Phase
        # 2.5 - BEFORE Phase 3 flips ``finalized`` - so a partial-finalize
        # failure can leave a non-``None`` strategy on an unfinalized type;
        # reading the stamp before this gate would mint an id in violation of
        # the helper's "finalized Relay-Node-shaped type" contract (spec-032
        # feedback P2).
        raise ConfigurationError(
            f"global_id_for: {definition.graphql_type_name} is not finalized; "
            "call finalize_django_types() (or build the schema) first - the "
            "GlobalID strategy is stamped at finalization.",
        )
    strategy = definition.effective_globalid_strategy
    if strategy is None:
        # Finalized but never stamped -> a non-Relay-Node DjangoType (the
        # stamp is written only for Relay-Node-shaped types).
        raise ConfigurationError(
            f"global_id_for: {definition.graphql_type_name} {_RELAY_NODE_GATE_LEAD} "
            f"{_RELAY_NODE_GATE_INHERIT_TAIL}",
        )
    if strategy not in STRING_GLOBALID_STRATEGIES:
        raise ConfigurationError(
            f"global_id_for: {definition.graphql_type_name} records the {strategy!r} "
            "GlobalID strategy, whose encoder runs on a live root this "
            "helper does not have, so it cannot promise the emitted payload. A "
            "consumer with a custom encoder owns its own test helper.",
        )
    # The string-strategy branches of ``encode_typename`` never touch
    # ``root`` (only the ``callable`` branch does, and it is unreachable here per
    # the gate above), so the payload comes from the exact code path the live
    # ``resolve_typename`` closure runs.
    payload = encode_typename(definition, strategy, type_cls, None)
    return str(relay.GlobalID(type_name=payload, node_id=str(id)))
