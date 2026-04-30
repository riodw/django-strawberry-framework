"""Type registry for ``DjangoType`` and choice-field enums.

Maps Django models to their generated ``DjangoType`` and ``(model,
field_name)`` to generated ``Enum`` classes. Used by:

- ``converters.convert_relation`` for forward-reference relation
  resolution when relating types are defined in any order.
- ``converters.convert_choices_to_enum`` for enum reuse across multiple
  ``DjangoType`` subclasses reading the same choice column.

The registry is a process-global singleton (``registry``). Test isolation
is via the ``clear()`` helper, typically wired into a ``pytest`` autouse
fixture.
"""

from collections.abc import Iterator
from enum import Enum
from typing import Any

from django.db import models

from .exceptions import ConfigurationError


class TypeRegistry:
    """Process-global registry of generated GraphQL types and enums."""

    def __init__(self) -> None:
        self._types: dict[type[models.Model], type] = {}
        self._models: dict[type, type[models.Model]] = {}
        self._enums: dict[tuple[type[models.Model], str], type[Enum]] = {}

    def register(self, model: type[models.Model], type_cls: type) -> None:
        """Register ``type_cls`` as the ``DjangoType`` for ``model``.

        Maintains both directions of the mapping so the optimizer can
        reverse a ``DjangoType`` class back to its Django model in O(1).

        Raises:
            ConfigurationError: ``model`` already has a registered type.
                The error message names the conflicting class so the
                consumer can identify the duplicate at import time.
        """
        if model in self._types:
            raise ConfigurationError(
                f"{model.__name__} is already registered as {self._types[model].__name__}",
            )
        self._types[model] = type_cls
        self._models[type_cls] = model

    def get(self, model: type[models.Model]) -> type | None:
        """Return the registered ``DjangoType`` for ``model``, or ``None``."""
        return self._types.get(model)

    def model_for_type(self, type_cls: type | None) -> type[models.Model] | None:
        """Reverse-lookup: return the Django model for a registered ``DjangoType``.

        Used by ``DjangoOptimizerExtension`` to trace a resolver's
        GraphQL return type back to a Django model so it can walk
        ``model._meta.get_fields()`` against the resolver's selection set.
        Returns ``None`` for unregistered classes (and for ``None`` itself,
        so the optimizer can pipeline through unwrapped wrapper types
        without an extra guard).
        """
        if type_cls is None:
            return None
        return self._models.get(type_cls)

    def iter_types(self) -> Iterator[tuple[type[models.Model], type]]:
        """Yield ``(model, type_cls)`` pairs for every registered ``DjangoType``.

        Public iterator so consumers (B6 schema audit, B7 walker) do not
        reach into ``_types`` directly. Keeps the internal dict shape
        private and provides a clean extension point for future filtering
        (e.g., schema-scoped registries).
        """
        yield from self._types.items()

    def lazy_ref(self, model: type[models.Model]) -> Any:
        """Return a forward reference resolved at schema build.

        Slice 3 deferred this in favor of eager resolution
        (``convert_relation`` calls ``registry.get`` and raises
        ``ConfigurationError`` if the target is unregistered). Lifting
        the dependency-order constraint requires picking one of:

        - ``Annotated["TargetType", strawberry.lazy("module.path")]`` so
          Strawberry resolves the type via a named import at schema
          build time. Best for cross-module references.
        - A string annotation (``"TargetType"``) that
          ``_build_annotations`` rewrites once all sibling types are
          registered. Simplest for same-module references.
        - A registry-tracked "pending relation" record that a
          ``finalize_types()`` post-processing pass resolves after every
          subclass has been seen.

        See the Post-slice-7 future work section in
        ``docs/spec-django_types.md`` for the full discussion.
        """
        # TODO(future): pick a forward-ref strategy from the docstring
        # above and wire it. The string-annotation approach is simplest
        # for same-module references; LazyType / Annotated is needed for
        # cross-module relations.
        raise NotImplementedError("lazy_ref pending future slice (definition-order independence)")

    def register_enum(
        self,
        model: type[models.Model],
        field_name: str,
        enum_cls: type[Enum],
    ) -> None:
        """Cache ``enum_cls`` for the ``(model, field_name)`` choice field.

        Two ``DjangoType``s pointing at the same choice column reuse the
        same enum, even if their consumer-facing class names differ.
        """
        self._enums[(model, field_name)] = enum_cls

    def get_enum(
        self,
        model: type[models.Model],
        field_name: str,
    ) -> type[Enum] | None:
        """Return the cached enum for ``(model, field_name)``, or ``None``."""
        return self._enums.get((model, field_name))

    def clear(self) -> None:
        """Drop all registered types and enums.

        Test-only — production code should never need to call this.
        Wire into a ``pytest`` autouse fixture (see
        ``tests/test_django_types.py``) so each test starts with a clean
        registry.
        """
        self._types.clear()
        self._models.clear()
        self._enums.clear()


registry = TypeRegistry()
