"""Exceptions raised by django-strawberry-framework.

Lives at the bottom of the import graph — no Django, no Strawberry, no
internal package imports — so the exception hierarchy can be raised from
anywhere without circulars.
"""

__all__ = (
    "ConfigurationError",
    "DjangoStrawberryFrameworkError",
    "OptimizerError",
)


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
        - A deferred-surface key (``filterset_class``, ``orderset_class``,
          ``aggregate_class``, ``fields_class``, ``search_fields``)
          declared before the spec that owns it has shipped.
        - Two ``DjangoType`` subclasses registering against the same model.
    """


class OptimizerError(DjangoStrawberryFrameworkError):
    """Raised when ``DjangoOptimizerExtension`` cannot plan a relation traversal.

    Most planning failures should be programmer errors caught early; a
    runtime ``OptimizerError`` typically signals a registry miss for a
    type that should have been registered by
    ``DjangoType.__init_subclass__``.
    """
