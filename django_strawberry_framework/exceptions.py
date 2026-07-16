"""Exceptions raised by django-strawberry-framework.

Lives at the bottom of the import graph - no Django, no Strawberry, no
internal package imports - so the exception hierarchy can be raised from
anywhere without circulars.
"""

from __future__ import annotations

__all__ = ("ConfigurationError", "DjangoStrawberryFrameworkError", "OptimizerError")


def _safe_type_name(value: object) -> str:
    """Return ``type(value).__name__`` without trusting hostile metaclass metadata."""
    try:
        name = type(value).__name__
    except BaseException:
        return "object"
    return name if isinstance(name, str) else "object"


def _safe_arg_repr(value: object) -> str:
    """``repr(value)`` if it succeeds, else a placeholder naming the arg type."""
    try:
        return repr(value)
    except BaseException:
        return f"<unprintable {_safe_type_name(value)}>"


class DjangoStrawberryFrameworkError(Exception):
    """Base exception for the package.

    Consumers can catch this to handle any framework-raised error in a
    single ``except``. Specific subclasses below distinguish causes when
    granular handling is needed.

    Rendering safety: the ORIGINAL message args are kept in ``self.args``
    (identity is authoritative - programmatic ``.args`` access sees the real
    objects), and ``str`` / ``repr`` are made safe at CALL TIME instead of
    sanitizing at construction. GraphQL-core's ``located_error`` wraps a
    non-``GraphQLError`` by calling ``str(original_error)``; if that raised, the
    typed framework exception would be replaced by a raw error on the wire and
    ``except ConfigurationError`` / ``except OptimizerError`` catchability would
    be destroyed. Overriding ``__str__`` / ``__repr__`` to render safely means:

    - a message arg whose ``__str__`` / ``__repr__`` fails only LATER (stateful)
      is still handled - the guard is at the render call, not at construction;
    - rendering is recomputed from the current ``args`` on each call, preserving
      standard exception behavior when callers replace ``args`` and preserving
      lazy-translation behavior when the active locale changes;
    - a ``BaseException`` (not just ``Exception``) raised by a hostile dunder is
      swallowed too - a display operation must never propagate ``SystemExit`` /
      ``KeyboardInterrupt`` and break wire identity.
    """

    def __str__(self) -> str:
        """Render ``str`` safely from the current args (see class docstring)."""
        try:
            rendered = super().__str__()
        except BaseException:
            rendered = (
                f"<unprintable {_safe_type_name(self.args[0])}>"
                if len(self.args) == 1
                else "(" + ", ".join(_safe_arg_repr(a) for a in self.args) + ")"
            )
        return rendered

    def __repr__(self) -> str:
        """Render ``repr`` safely from the current args (see class docstring)."""
        try:
            rendered = super().__repr__()
        except BaseException:
            args = ", ".join(_safe_arg_repr(a) for a in self.args)
            rendered = f"{_safe_type_name(self)}({args})"
        return rendered


class ConfigurationError(DjangoStrawberryFrameworkError):
    """Raised when consumer configuration is invalid or inconsistent.

    Covers type-creation / finalization Meta validation, settings reads,
    registry collisions, filter/order/mutation set wiring, and other
    configuration-time failures. Examples:

        - Missing ``Meta.model``.
        - ``fields`` and ``exclude`` declared together.
        - A deferred-surface key (``aggregate_class``, ``fields_class``,
          ``search_fields``) declared before the spec that owns it has
          shipped.
        - Two ``DjangoType`` subclasses registering against the same model.
        - A non-mapping ``DJANGO_STRAWBERRY_FRAMEWORK`` settings value.

    ``SyncMisuseError`` (defined in ``utils/querysets.py``, re-exported at
    the package root) multiple-inherits this class and ``RuntimeError`` for
    async-hook-from-sync misuse.
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
        - Window fetch-mode contract: ``utils/connections.py::
          assert_window_fetch_mode`` rejects a window that engages the
          count-free ``hasNextPage`` probe while also annotating the partition
          count (a planner/strategy bug that would otherwise pass the n+1
          sentinel through as a real edge).
        - Window bounds: ``utils/connections.py::window_range_plan`` rejects
          a negative offset or limit on a direct window request.
    """
