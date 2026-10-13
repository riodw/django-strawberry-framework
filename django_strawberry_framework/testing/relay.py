"""Public Relay test helpers - ``global_id_for`` / ``decode_global_id``.

The two helpers consumer test suites use to mint and assert the durable
``GlobalID``s the ``0.0.9`` strategy system emits (``docs/SPECS/spec-032-full_relay-0_0_9.md``
Decision 10). Lives under ``testing/`` (not the package root) because the
audience is consumer *test suites*; the export was withheld in ``0.0.9``'s
spec-031 cycle until this card shipped the consumer (the tested-usage
promotion discipline).

- ``global_id_for(type_cls, id, *, schema=None)`` mints the encoded
  ``GlobalID`` string a **finalized Relay-Node-shaped** type emits for a pk.
  The payload follows the type's finalize-stamped strategy: ``model`` /
  ``type+model`` emit the model label (``app_label.modelname``); ``type`` emits
  the GraphQL type name - under ``schema`` the name that schema published for
  the type (the slot its ``id`` field emits, whatever ``NameConverter`` the
  schema runs); with no schema the ``graphql_type_name``, the default
  converter's spelling, which is the live slot exactly when no consumer
  converter renames the type. ``callable`` / ``custom`` raise
  ``ConfigurationError`` - those encoders run on a live ``root`` the helper
  does not have, so it cannot promise the emitted payload (a consumer with a
  custom encoder owns its own test helper). Finalize first: the strategy is
  stamped at finalization, so an unfinalized type (and a finalized
  non-Relay-Node type) raises too.
- ``decode_global_id(gid, *, schema=None)`` is the public re-export of
  ``django_strawberry_framework.types.relay.decode_global_id`` - same uniform
  ``ConfigurationError`` contract and ``(target_type, node_id)`` return; the
  internal signature is already consumer-shaped. Pass the schema the id came
  from for a ``type``-strategy id minted under a type-renaming converter.

Asymmetry contract (Decision 10): a SECONDARY model-label
emitter mints the payload it genuinely emits, while decode routes that same
payload to the model's PRIMARY via ``registry.get(model)`` - so
``decode_global_id(global_id_for(T, pk)) == (T, str(pk))`` holds only for
lone/primary model-label types and for ``type``-strategy payloads (both calls
given the same ``schema``, or neither). Documented, not "fixed": it is exactly
the routing a live ``node(id:)`` performs on the same id.

Importing this submodule (not ``testing/__init__``) is the public path; it
also keeps ``import django_strawberry_framework.testing`` light - the
``types``-package imports below are paid only by suites that use the helpers.
"""

from typing import TYPE_CHECKING, cast

from strawberry import relay

from django_strawberry_framework.exceptions import ConfigurationError, _safe_arg_repr
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.base import (
    _RELAY_NODE_GATE_INHERIT_TAIL,
    _RELAY_NODE_GATE_LEAD,
    STRING_GLOBALID_STRATEGIES,
    DjangoType,
)
from django_strawberry_framework.types.relay import (
    decode_global_id,
    encode_typename,
    published_node_type_name,
)

if TYPE_CHECKING:
    from strawberry.schema import Schema

    from django_strawberry_framework.types.definition import DjangoTypeDefinition

__all__ = ["decode_global_id", "global_id_for"]


def global_id_for(
    type_cls: type[object],
    id: object,  # noqa: A002
    *,
    schema: "Schema | None" = None,
) -> str:
    """Return the encoded ``GlobalID`` string ``type_cls`` emits for ``id``.

    Reads the finalize-stamped ``effective_globalid_strategy`` (never the
    setting), so the helper is consistent-by-construction with live emission;
    under a ``type`` strategy the slot is the name ``schema`` published for the
    type when a schema is given (``ConfigurationError`` if that schema publishes
    no Relay-Node object type for it), else the ``graphql_type_name``. Raises
    ``ConfigurationError`` for non-``DjangoType`` inputs, unfinalized types,
    finalized non-Relay-Node types, and ``callable`` / ``custom`` strategies
    (see the module docstring for the full contract).
    """
    # Bound before the ``try``: the gate below passes only when the ``try`` completed,
    # which rebinds it to the class's own attribute.
    definition: object = None
    try:
        # basedpyright: trust boundary: ``type_cls: type[object]`` is the public contract; the
        # class check validates a test call that breaks it
        is_django_type = isinstance(type_cls, type) and issubclass(type_cls, DjangoType)  # pyright: ignore[reportUnnecessaryIsInstance]
        definition = getattr(type_cls, "__django_strawberry_definition__", None)
        registered_definition = registry.get_definition(type_cls) if is_django_type else None
        is_registered_own_definition = (
            definition is not None
            and definition is registered_definition
            and getattr(definition, "origin", None) is type_cls
        )
    except BaseException:
        is_registered_own_definition = False
    if not is_registered_own_definition:
        raise ConfigurationError(
            f"global_id_for: {_safe_arg_repr(type_cls)} is not a registered "
            "DjangoType subclass; "
            "pass the DjangoType class whose emitted id you want to mint.",
        )
    # The gate above proved ``definition`` is ``type_cls``'s own registered one.
    definition = cast("DjangoTypeDefinition", definition)
    if not definition.finalized:
        # Gate on ``finalized`` FIRST. The strategy stamp is written in Phase
        # 2.5 - BEFORE Phase 3 flips ``finalized`` - so a partial-finalize
        # failure can leave a non-``None`` strategy on an unfinalized type;
        # reading the stamp before this gate would mint an id in violation of
        # the helper's "finalized Relay-Node-shaped type" contract.
        raise ConfigurationError(
            f"global_id_for: {definition.graphql_type_name} is not finalized; "
            "call finalize_django_types() first (directly, or by importing a "
            "schema module that calls it) - the GlobalID strategy is stamped "
            "at finalization.",
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
    if strategy == "type" and schema is not None:
        # The live ``type`` slot is Strawberry's ``info.path.typename``: the name
        # the executing schema published for the type. Read it off that schema's
        # published map, the same authority the decoder resolves it through.
        published = published_node_type_name(schema, type_cls)
        if published is None:
            raise ConfigurationError(
                f"global_id_for: {definition.graphql_type_name} is not published as a "
                "Relay-Node object type by the given schema; pass the schema whose "
                "emitted id you want to mint.",
            )
        return str(relay.GlobalID(type_name=published, node_id=str(id)))
    # The string-strategy branches of ``encode_typename`` never touch
    # ``root`` (only the ``callable`` branch does, and it is unreachable here per
    # the gate above), so the model-label payload comes from the exact code path
    # the live ``resolve_typename`` closure runs; the schema-less ``type`` payload
    # is the default converter's spelling of the type name.
    # The gate above proved ``definition.origin is type_cls``.
    payload = encode_typename(definition, strategy, definition.origin, None)
    return str(relay.GlobalID(type_name=payload, node_id=str(id)))
