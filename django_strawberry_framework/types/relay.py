"""Internal Relay/interface helpers for the 0.0.5 Relay foundation slice."""

from __future__ import annotations


def install_is_type_of(type_cls: type) -> None:
    """Borrow strawberry-django's ``is_type_of`` virtual-subclass behavior.

    Direct port of ``strawberry_django/type.py:203-211``. Strawberry's
    interface dispatch uses ``is_type_of`` to identify the concrete type
    for a returned ORM instance. Without this borrow, an interface field
    that returns a Django model can fail Strawberry's isinstance check
    and surface as "Cannot determine type for object of model X" at
    runtime (spec Decision 6, line 351).

    Preserves a consumer-declared ``is_type_of`` via the ``cls.__dict__``
    membership check (the same discriminator strawberry-django uses); a
    function inherited from a base does not count as "declared on this
    class" and is overwritten by the framework default.

    The upstream ``get_strawberry_type_cast`` branch is intentionally
    omitted — our package does not yet expose ``strawberry.cast(...)``
    integration anywhere else, and adding it now would couple this slice
    to a Strawberry surface we have not committed to. If a future adopter
    needs ``strawberry.cast(...)`` support, a focused follow-up slice can
    add the branch without churn to the rest of the Relay machinery.
    """
    if "is_type_of" in type_cls.__dict__:
        return
    model = type_cls.__django_strawberry_definition__.model

    def is_type_of(obj: object, info: object) -> bool:
        return isinstance(obj, (type_cls, model))

    type_cls.is_type_of = is_type_of


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
