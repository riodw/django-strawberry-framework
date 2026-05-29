"""Mixins shared across the FilterSet / OrderSet / AggregateSet / FieldSet family.

Ported from ``django_graphene_filters/mixins.py`` and refactored to this
package's structure (Strawberry, not Graphene) and dependencies. This module
lives at the package root so the ``filters`` subpackage -- and the future
``orders`` / ``aggregates`` / ``fields`` subpackages (``WIP-ALPHA-022`` and
later) -- all import shared set-machinery from one neutral home rather than
from each other.

Scope is deliberately limited to the two mixins the shipped ``FilterSet``
already uses:

- ``ClassBasedTypeNameMixin`` -- class-derived GraphQL type naming
  (``type_name_for``), the single naming rule every set's arguments factory
  shares (the cookbook uses it for filterset, orderset, AND aggregateset).
- ``LazyRelatedClassMixin`` -- string / callable class-reference resolution
  used by ``RelatedFilter`` (and, later, ``RelatedOrder`` / ``RelatedAggregate``).

The cookbook's other shared helpers (``get_concrete_field_names``,
``InputObjectTypeFactoryMixin``, ``ObjectTypeFactoryMixin``) are intentionally
NOT ported yet: the ``FilterSet`` does not use them today, and the package's
100%-coverage gate would flag them as dead. They land with their consuming
sets.
"""

from __future__ import annotations

from typing import Any

from django.db.models.constants import LOOKUP_SEP
from django.utils.module_loading import import_string

from .utils.strings import pascal_case


class ClassBasedTypeNameMixin:
    """Contribute a ``type_name_for()`` classmethod for class-derived GraphQL naming.

    Subclasses tune two class attributes:

    - ``_root_type_suffix`` -- appended to ``cls.__name__`` for the root type
      (``FilterSet`` keeps the default ``"InputType"`` -> ``FooFilterInputType``).
    - ``_field_type_suffix`` -- appended after a PascalCased field path for the
      per-field operator-bag type (``FilterSet`` overrides to
      ``"FilterInputType"`` -> ``FooFilterBarFilterInputType``).

    A single implementation handles both the root name (``field_path is None``)
    and a ``LOOKUP_SEP``-separated nested path. Centralising it here means the
    future ``OrderSet`` / ``AggregateSet`` reuse the exact same naming rule with
    their own suffixes instead of re-deriving the convention inline.

    Port of ``django_graphene_filters/mixins.py::ClassBasedTypeNameMixin``,
    using this package's ``utils.strings.pascal_case`` in place of the
    cookbook's ``stringcase.pascalcase``.
    """

    _root_type_suffix: str = "InputType"
    _field_type_suffix: str = "InputType"

    @classmethod
    def type_name_for(cls, field_path: str | None = None) -> str:
        """Return the GraphQL type name for this class, or for a sub-field path."""
        if field_path is None:
            return f"{cls.__name__}{cls._root_type_suffix}"
        pascal = "".join(pascal_case(part) for part in field_path.split(LOOKUP_SEP))
        return f"{cls.__name__}{pascal}{cls._field_type_suffix}"


class LazyRelatedClassMixin:
    """Resolve a class reference that may be a string, callable, or class.

    Verbatim port of `django_graphene_filters/mixins.py::LazyRelatedClassMixin`.
    Used by `RelatedFilter` to break cycles between filtersets declared in
    the same module without forcing an `if TYPE_CHECKING` dance on the
    consumer.
    """

    def resolve_lazy_class(self, class_ref: Any, bound_class: type | None) -> Any:
        """Resolve `class_ref` to a class.

        Strings resolve via two attempts:

        1. As an absolute import path through `import_string`.
        2. On `ImportError`, prefixed with `bound_class.__module__` so an
           unqualified `"ManagerFilter"` resolves against the owning
           filterset's module.

        Callables that are not classes are invoked as zero-arg factories;
        everything else is returned as-is.
        """
        if isinstance(class_ref, str):
            try:
                return import_string(class_ref)
            except ImportError:
                if bound_class:
                    path = ".".join([bound_class.__module__, class_ref])
                    return import_string(path)
                raise
        elif callable(class_ref) and not isinstance(class_ref, type):
            return class_ref()
        return class_ref


__all__ = ("ClassBasedTypeNameMixin", "LazyRelatedClassMixin")
