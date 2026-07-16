"""Mutations subsystem - the write side (spec-036).

A five-module subpackage in the spirit of ``filters/`` / ``orders/`` (Decision 4's
``inputs`` / ``sets`` / ``resolvers`` / ``fields`` quartet plus ``permissions.py``
for Decision 15 write-auth):

- ``inputs.py`` - generated ``<Model>Input`` / ``<Model>PartialInput`` classes,
  the public ``FieldError`` envelope, and the ``<Name>Payload`` wrapper.
- ``sets.py`` - the ``DjangoMutation`` base, its metaclass ``Meta`` validation,
  and the finalizer phase-2.5 bind.
- ``permissions.py`` - ``DjangoModelPermission``, the DRF-shaped default
  write-authorization class.
- ``resolvers.py`` - the sync + async create / update / delete pipeline.
- ``fields.py`` - the ``DjangoMutationField`` factory.

Re-exports ``FieldError``, ``DjangoMutation``, ``DjangoModelPermission``, and
``DjangoMutationField`` - the four-symbol mutation public surface. Eager
re-export + typed ``__all__`` matches the ``forms/__init__.py`` package-marker
shape (filters / orders add Decision-11 helpers this file does not need).
"""

from __future__ import annotations

from .fields import DjangoMutationField
from .inputs import FieldError
from .permissions import DjangoModelPermission
from .sets import DjangoMutation

__all__: tuple[str, ...] = (
    "DjangoModelPermission",
    "DjangoMutation",
    "DjangoMutationField",
    "FieldError",
)
