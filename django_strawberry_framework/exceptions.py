"""Exceptions raised by django-strawberry-framework.

Lives at the bottom of the import graph - no Django, no Strawberry, no
internal package imports - so the exception hierarchy can be raised from
anywhere without circulars.
"""

from __future__ import annotations

__all__ = (
    "ConfigurationError",
    "DjangoStrawberryFrameworkError",
    "LookupValidationError",
    "OptimizerError",
    "PathResolutionError",
)


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


class PathResolutionError(ConfigurationError):
    """Raised when a model-field path cannot be strictly classified.

    Subclasses ``ConfigurationError`` (not ``OptimizerError``): a path that
    fails strict classification is a definition-time defect in a
    framework-generated or consumer-declared traversal, not a runtime planning
    failure - it belongs to the same configuration/definition family as a
    malformed ``Meta`` declaration, and remains catchable through the package
    base and through ``ConfigurationError``.

    The single named error for strict path classification. Distinct from the
    lenient boolean ``utils/relations.py::path_traverses_to_many`` walk (which
    swallows resolution failure and answers ``False``) so strict callers never
    turn a malformed declaration into a lenient "does not traverse many"
    answer by accident.

    Raise sites (all in ``utils/relations.py::classify_path``):

        - A segment that ``Model._meta.get_field`` rejects (``FieldDoesNotExist``),
          including a hidden reverse relation declared ``related_name="+"``.
        - A non-relation (scalar) segment that is NOT the final segment - the
          path continues past a column that cannot be traversed.
        - A forward ``GenericForeignKey`` segment (``is_relation=True`` but no
          ``path_infos``), whether terminal or mid-path - it is neither a
          scalar terminal nor a traversable relation.
        - A relation segment whose ``path_infos`` is empty.

    The message always names the model label, the complete declared path, and
    the offending segment so a lenient caller cannot silently downgrade it.
    """

    def __init__(
        self,
        model: object,
        field_path: str,
        segment: str,
    ) -> None:
        model_label = getattr(getattr(model, "_meta", None), "label", None) or _safe_type_name(
            model,
        )
        super().__init__(
            f"Cannot classify path {field_path!r} on model {model_label}: "
            f"segment {segment!r} is not a traversable model-field relation.",
        )
        self.model = model
        self.field_path = field_path
        self.segment = segment


class LookupValidationError(ConfigurationError):
    """Raised when a django-filter lookup expression is invalid for a terminal.

    Distinct from ``PathResolutionError``: path classification and lookup
    validation are separate contracts, so a caller can tell "the relation path
    does not resolve" apart from "the path resolves but this transform/lookup
    is not available on its output field". Both are configuration-family
    (subclass ``ConfigurationError``), catchable through the package base.

    Raised by ``utils/relations.py::validate_lookup_expr`` when:

        - ``lookup_expr`` is empty, or splitting it on ``LOOKUP_SEP`` yields an
          empty part (e.g. ``"date__"`` or a leading ``"__"``).
        - A non-final part does not resolve as a transform on the current
          output field (``get_transform`` returns ``None``).
        - The final part resolves as neither a lookup (``get_lookup``) nor a
          trailing transform whose output supports the implicit ``exact``.

    The message names the terminal field, the full ``lookup_expr``, and the
    offending part so the failure is actionable.
    """

    def __init__(
        self,
        terminal: object,
        lookup_expr: str,
        part: str,
    ) -> None:
        terminal_label = getattr(terminal, "name", None) or _safe_type_name(terminal)
        super().__init__(
            f"Invalid lookup expression {lookup_expr!r} for terminal "
            f"{terminal_label}: part {part!r} is not a valid transform or lookup.",
        )
        self.terminal = terminal
        self.lookup_expr = lookup_expr
        self.part = part


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
        - Window partition resolution: ``optimizer/plans.py::
          window_partition_for_prefetch`` rejects a relation whose join kind is
          not windowable, or one for which no parent partition expression can be
          resolved (both signal a fall back to per-parent resolution).
        - Reversed keyset window: ``optimizer/plans.py::apply_window_pagination``
          rejects a keyset-seek window that is also reversed, since backward
          keyset pagination resolves through the per-parent/root slicer, never a
          reversed window plan.
        - Row-preserving predicate attachment
          (``optimizer/predicates.py::attach_exists``): the three runtime
          caller-contract guards - inner-queryset model does not match the outer
          model, inner and outer resolve to different database aliases, or the
          outer queryset carries a combinator (union / intersection /
          difference) that a reserved existence alias cannot attach to.
    """
