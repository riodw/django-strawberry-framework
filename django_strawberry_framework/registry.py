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

from enum import Enum
from typing import Any

from django.db import models

from .exceptions import ConfigurationError


class TypeRegistry:
    """Process-global registry of generated GraphQL types and enums."""

    def __init__(self) -> None:
        self._types: dict[type[models.Model], type] = {}
        self._enums: dict[tuple[type[models.Model], str], type[Enum]] = {}

    def register(self, model: type[models.Model], type_cls: type) -> None:
        """Register ``type_cls`` as the ``DjangoType`` for ``model``.

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

    def get(self, model: type[models.Model]) -> type | None:
        """Return the registered ``DjangoType`` for ``model``, or ``None``."""
        return self._types.get(model)

    def lazy_ref(self, model: type[models.Model]) -> Any:
        """Return a forward reference resolved at schema build.

        Used during relation conversion when the target ``DjangoType`` may
        not yet be registered. Resolution happens lazily when Strawberry
        materializes the schema.

        Slice 3 will pick one of these mechanisms:

        - Return ``Annotated["TargetType", strawberry.lazy("module.path")]``
          so Strawberry resolves the type via a named import at schema
          build time. Best for cross-module references.
        - Return a string annotation (``"TargetType"``) that
          ``_build_annotations`` rewrites once all sibling types are
          registered. Simplest for same-module references.
        - Register a "pending relation" record on the registry that
          ``DjangoType.__init_subclass__`` post-processes after every
          subclass has been seen.
        """
        # TODO(slice 3): pick a forward-ref strategy from the docstring
        # and wire it. The string-annotation approach is simplest for
        # same-module references; LazyType / Annotated is needed for
        # cross-module relations.
        raise NotImplementedError("lazy_ref pending Slice 3 (relation conversion)")

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
        self._enums.clear()


registry = TypeRegistry()
