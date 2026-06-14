"""Exceptions raised by django-strawberry-framework.

Lives at the bottom of the import graph - no Django, no Strawberry, no
internal package imports - so the exception hierarchy can be raised from
anywhere without circulars.
"""

__all__ = ("ConfigurationError", "DjangoStrawberryFrameworkError", "OptimizerError")


class DjangoStrawberryFrameworkError(Exception):
    """Base exception for the package.

    Consumers can catch this to handle any framework-raised error in a
    single ``except``. Specific subclasses below distinguish causes when
    granular handling is needed.
    """


class ConfigurationError(DjangoStrawberryFrameworkError):
    """Raised when a ``DjangoType.Meta`` is malformed.

    Examples:
        - Missing ``Meta.model``.
        - ``fields`` and ``exclude`` declared together.
        - A deferred-surface key (``aggregate_class``, ``fields_class``,
          ``search_fields``) declared before the spec that owns it has
          shipped.
        - Two ``DjangoType`` subclasses registering against the same model.
    """


class OptimizerError(DjangoStrawberryFrameworkError):
    """Raised when ``DjangoOptimizerExtension`` cannot plan a relation traversal.

    Raise sites:
        - Typed input-guard at construction: ``FieldMeta.from_django_field``
          rejects an input that is not a Django field descriptor (missing
          ``name`` / ``is_relation``), converting an otherwise late
          ``AttributeError`` into a typed, call-site failure naming the bad
          input.
        - Strictness-``"raise"`` N+1 guard: fires when optimizer
          ``strictness`` is ``"raise"`` and a request reaches an unplanned
          relation that would lazy-load. Covers both the list-relation
          resolver and the nested-connection window-partition path (a
          single-valued forward relation or any kind without a windowable
          parent partition).
    """
