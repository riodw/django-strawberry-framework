"""Internal Relay/interface helpers for the 0.0.5 Relay foundation slice."""

from __future__ import annotations

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# implement ``install_is_type_of`` using strawberry-django's virtual subclass
# pattern, preserving any consumer-declared ``is_type_of``.

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# implement ``apply_interfaces`` to inject accepted Strawberry interfaces into
# ``DjangoType`` bases before ``strawberry.type(...)`` finalization.

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# implement ``implements_relay_node`` and ``install_relay_node_resolvers`` with
# the ``__func__`` identity test so consumer Relay resolver overrides win.

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# implement ``_resolve_id_attr_default`` and ``_resolve_id_default`` with
# Strawberry ``NodeID`` fallback support and Django ``__dict__`` cache reads.

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# implement sync/async ``_resolve_node_default`` and ``_resolve_nodes_default``
# using the model default manager, ``DjangoType.get_queryset``, optional
# optimizer cooperation, order preservation, and required-missing semantics.
