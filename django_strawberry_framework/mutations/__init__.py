"""Mutations subsystem - the write side (spec-036).

A four-module subpackage in the spirit of ``filters/`` / ``orders/`` (the
module names differ per spec-036 Decision 4):

- ``inputs.py`` (Slice 1) - generated ``<Model>Input`` / ``<Model>PartialInput``
  classes, the public ``FieldError`` envelope, and the ``<Name>Payload`` wrapper.
- ``sets.py`` (Slice 2) - the ``DjangoMutation`` base, its metaclass ``Meta``
  validation, and the finalizer phase-2.5 bind.
- ``permissions.py`` (Slice 2) - ``DjangoModelPermission``, the DRF-shaped default
  write-authorization class.
- ``resolvers.py`` (Slice 3) - the sync + async create / update / delete pipeline.
- ``fields.py`` (Slice 3) - the ``DjangoMutationField`` factory.

This slice re-exports ``FieldError`` (Slice 1), ``DjangoMutation`` +
``DjangoModelPermission`` (Slice 2), and now ``DjangoMutationField`` (Slice 3) -
the four-symbol mutation public surface is complete. Mirrors the
``filters/__init__.py`` / ``orders/__init__.py`` re-export idiom.
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
