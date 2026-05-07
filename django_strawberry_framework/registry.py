"""Type registry for ``DjangoType`` metadata, pending relations, and choice enums.

Maps Django models to their generated ``DjangoType`` and ``(model,
field_name)`` to generated ``Enum`` classes. Used by:

- ``converters.convert_relation`` for relation resolution once target
  types are registered.
- ``converters.convert_choices_to_enum`` for enum reuse across multiple
  ``DjangoType`` subclasses reading the same choice column.

The registry is a process-global singleton (``registry``). Test isolation
is via the ``clear()`` helper, typically wired into a ``pytest`` autouse
fixture.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import Enum
from typing import TYPE_CHECKING

from django.db import models

from .exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: no cover
    from .types.definition import DjangoTypeDefinition
    from .types.relations import PendingRelation


class TypeRegistry:
    """Process-global registry of generated GraphQL types and enums.

    Mutations (``register``, ``register_enum``, ``clear``) are not guarded
    by a lock.  This is safe because every production-path mutation runs
    at import time from ``DjangoType.__init_subclass__`` (single-threaded
    module loading); ``clear`` is test-only.  Do not call ``register`` or
    ``register_enum`` from a request handler or async resolver.
    """

    def __init__(self) -> None:
        self._types: dict[type[models.Model], type] = {}
        self._models: dict[type, type[models.Model]] = {}
        self._enums: dict[tuple[type[models.Model], str], type[Enum]] = {}
        self._definitions: dict[type, DjangoTypeDefinition] = {}
        self._pending: list[PendingRelation] = []
        self._finalized: bool = False

    def register(self, model: type[models.Model], type_cls: type) -> None:
        """Register ``type_cls`` as the ``DjangoType`` for ``model``.

        Maintains both directions of the mapping so the optimizer can
        reverse a ``DjangoType`` class back to its Django model in O(1).

        Raises:
            ConfigurationError: ``model`` already has a registered type,
                or ``type_cls`` is already registered against a different
                model.  The error message names the conflicting class or
                model so the consumer can identify the duplicate at
                import time.
        """
        if model in self._types:
            raise ConfigurationError(
                f"{model.__name__} is already registered as {self._types[model].__name__}",
            )
        existing_model = self._models.get(type_cls)
        if existing_model is not None and existing_model is not model:
            raise ConfigurationError(
                f"{type_cls.__name__} is already registered against {existing_model.__name__}",
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

    def register_definition(self, type_cls: type, definition: DjangoTypeDefinition) -> None:
        """Register the collected definition object for ``type_cls``."""
        existing = self._definitions.get(type_cls)
        if existing is not None and existing is not definition:
            raise ConfigurationError(f"{type_cls.__name__} already has a registered DjangoTypeDefinition")
        self._definitions[type_cls] = definition

    def get_definition(self, type_cls: type) -> DjangoTypeDefinition | None:
        """Return the collected definition for ``type_cls``, or ``None``."""
        return self._definitions.get(type_cls)

    def iter_definitions(self) -> Iterator[tuple[type, DjangoTypeDefinition]]:
        """Yield ``(type_cls, definition)`` pairs in registration order."""
        yield from self._definitions.items()

    def add_pending_relation(self, pending: PendingRelation) -> None:
        """Record a relation whose target type must be resolved during finalization."""
        self._pending.append(pending)

    def iter_pending_relations(self) -> Iterator[PendingRelation]:
        """Yield pending relation records in collection order."""
        yield from self._pending

    def discard_pending(self, resolved: Iterable[PendingRelation]) -> None:
        """Drop pending records that have been resolved successfully."""
        resolved_list = list(resolved)
        self._pending = [pending for pending in self._pending if pending not in resolved_list]

    def is_finalized(self) -> bool:
        """Return whether the registry has completed ``finalize_django_types()``."""
        return self._finalized

    def mark_finalized(self) -> None:
        """Mark the registry as finalized."""
        self._finalized = True

    def register_enum(
        self,
        model: type[models.Model],
        field_name: str,
        enum_cls: type[Enum],
    ) -> None:
        """Cache ``enum_cls`` for the ``(model, field_name)`` choice field.

        Two ``DjangoType``s pointing at the same choice column reuse the
        same enum, even if their consumer-facing class names differ.

        Raises:
            ConfigurationError: an enum is already cached for
                ``(model, field_name)`` and it is a different class.
                Re-registering the *same* enum class is a no-op so the
                normal ``get_enum``-then-``register_enum`` cache pattern
                in ``convert_choices_to_enum`` still works under retry.
        """
        key = (model, field_name)
        existing = self._enums.get(key)
        if existing is not None and existing is not enum_cls:
            raise ConfigurationError(
                f"{model.__name__}.{field_name} is already registered as {existing.__name__}",
            )
        self._enums[key] = enum_cls

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
        self._definitions.clear()
        self._pending.clear()
        self._finalized = False


registry = TypeRegistry()
