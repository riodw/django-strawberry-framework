"""Tests for the 0.0.5 Relay interfaces slice."""

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# add validation/storage coverage for accepted interfaces, single-interface
# class normalization, rejected malformed ``Meta.interfaces`` values,
# duplicate entries, DjangoType self-references, empty tuples, direct Relay
# inheritance, and composite primary keys.

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# add Relay behavior coverage for id annotation suppression, default resolver
# injection, consumer override preservation, NodeID annotations, non-Relay
# interfaces, ``get_queryset`` cooperation, sync lookup, and async lookup.

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# add ``is_type_of`` coverage for both Relay and non-Relay DjangoTypes while
# proving consumer-declared ``is_type_of`` methods are preserved.
