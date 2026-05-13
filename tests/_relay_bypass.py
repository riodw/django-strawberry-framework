"""Slice 4 bypass helper for staging ``Meta.interfaces`` on a registered ``DjangoType``.

Slice 4 cannot declare ``Meta.interfaces = (relay.Node,)`` end-to-end while
``"interfaces"`` is still in ``DEFERRED_META_KEYS`` (Slice 5 promotes the
key). Each Slice 4 test instead registers a plain ``DjangoType`` and then
stages the interfaces tuple directly on ``DjangoTypeDefinition.interfaces``
after registration.

Two steps are load-bearing:

1. Set ``definition.interfaces`` so Phase 2.5 of ``finalize_django_types()``
   reads the tuple and runs ``apply_interfaces`` / the composite-pk gate /
   the resolver-injection step.
2. Strip the synthesized ``id`` annotation from ``type_cls.__annotations__``
   when ``relay.Node`` is being staged. Slice 3's ``_build_annotations``
   strips this at class-creation time when ``Meta.interfaces`` already
   names ``relay.Node``; because the bypass runs after ``__init_subclass__``
   it has to strip the annotation itself or Strawberry will reject the
   schema with an ``id: Int!`` vs ``id: GlobalID!`` interface clash.

Once Slice 5 promotes ``"interfaces"`` and consumers can declare
``Meta.interfaces`` end-to-end, this helper becomes a structural no-op and
the call sites collapse to direct ``Meta`` declarations.

This module lives under ``tests/`` and is imported only by package tests
(``tests/...``) and HTTP tests (``examples/fakeshop/test_query/...``). It
is NOT part of the package source surface; no public re-export.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from strawberry import relay

from django_strawberry_framework.registry import registry

if TYPE_CHECKING:
    pass


def stage_relay_definition(
    type_cls: type,
    interfaces: tuple[type, ...] = (relay.Node,),
) -> None:
    """Stage ``interfaces`` on a registered ``DjangoType`` plus the pk strip.

    See module docstring for the why. The default ``(relay.Node,)`` covers
    the Relay-node-shaped majority of Slice 4 tests; pass a different
    tuple for non-Relay-interface coverage (e.g. ``(Auditable,)``).
    """
    definition = registry.get_definition(type_cls)
    assert definition is not None, f"{type_cls.__name__} is not registered in the registry"
    definition.interfaces = interfaces
    if relay.Node in interfaces:
        pk_attname = definition.model._meta.pk.name
        type_cls.__annotations__.pop(pk_attname, None)
