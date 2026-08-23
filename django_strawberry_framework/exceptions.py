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
    """Return the name identifying ``value``'s kind, without trusting its metadata.

    A class names itself. Reporting its metaclass instead would put ``ModelBase``
    in front of every Django model and ``type`` in front of every plain class,
    identifying nothing in the one diagnostic a consumer has left, so a class
    contributes its own ``__name__`` and any other object contributes its type's.
    A class whose own ``__name__`` is unreadable or non-string falls back to the
    metaclass name before the ``"object"`` last resort, so the caller still gets
    the most specific label that can be rendered safely.
    """
    try:
        is_type = isinstance(value, type)
    except BaseException:
        is_type = False
    sources = (value, type(value)) if is_type else (type(value),)
    for source in sources:
        try:
            name = source.__name__
        except BaseException:
            continue
        try:
            is_str_name = isinstance(name, str)
        except BaseException:
            is_str_name = False
        if not is_str_name:
            continue
        try:
            if not name:
                continue
            # A metaclass can return a ``str`` subclass for ``__name__``.  Returning
            # that object would let its ``__str__`` / ``__format__`` run while a
            # typed error message is being assembled, replacing the framework error
            # with an arbitrary consumer exception.  The base ``str`` slot strips
            # the subclass before the value reaches any f-string or join operation.
            return str.__str__(name)
        except BaseException:
            continue
    return "object"


def _safe_arg_repr(value: object) -> str:
    """``repr(value)`` if it succeeds, else a placeholder naming the arg type."""
    try:
        return str.__str__(repr(value))
    except BaseException:
        return f"<unprintable {_safe_type_name(value)}>"


def _safe_class_name(value: object, *, qualified: bool = False) -> str:
    """Return a class label without trusting hostile metaclass metadata.

    The one class-label renderer error-message assembly shares (``types/relay.py``
    and ``types/finalizer.py`` import it; the sealed-queryset boundary in
    ``utils/querysets.py`` deliberately keeps a stricter local variant whose
    non-string fallback never dispatches the name object at all). A ``str``
    subclass ``__name__`` is read through the base ``str`` slot so its overridden
    ``__str__`` never runs; an unreadable ``__name__`` degrades to
    ``_safe_type_name``; a non-string one renders through the guarded repr.
    """
    attribute = "__qualname__" if qualified else "__name__"
    try:
        name = getattr(value, attribute)
    except BaseException:
        return _safe_type_name(value)
    try:
        if isinstance(name, str) and name:
            return str.__str__(name)
    except BaseException:
        pass
    return _safe_arg_repr(name)


def _safe_model_label(model: object) -> str:
    """Return a model label without trusting consumer-supplied metadata."""
    try:
        meta = getattr(model, "_meta", None)
        label = getattr(meta, "label", None)
    except BaseException:
        return _safe_type_name(model)
    try:
        if isinstance(label, str):
            label_str = str(label)
            return str.__str__(label_str) or _safe_type_name(model)
    except BaseException:
        pass
    return _safe_type_name(model)


def _safe_terminal_label(terminal: object) -> str:
    """Return a terminal field name without trusting consumer-supplied metadata."""
    try:
        name = getattr(terminal, "name", None)
    except BaseException:
        return _safe_type_name(terminal)
    try:
        if isinstance(name, str):
            name_str = str(name)
            return str.__str__(name_str) or _safe_type_name(terminal)
    except BaseException:
        pass
    return _safe_type_name(terminal)


def describe_value(value: object) -> str:
    """Render ``value`` as an error message's ``got <this>`` tail, without ever raising.

    The shared renderer for the ``got {type} {value!r}`` tail a typed rejection
    appends to its prose, so a rejection message cannot itself fail on the value
    it is rejecting. That is a real failure mode rather than a defensive
    flourish, because the tail is built by an f-string at the RAISE SITE - before
    any exception object exists, so the ``__str__`` / ``__repr__`` guards on
    ``DjangoStrawberryFrameworkError`` cannot help:

    - a consumer-supplied object with a hostile or stateful ``__repr__`` raises
      while the message is being formatted; and
    - CPython 3.11+ refuses to convert an integer with more than
      ``sys.get_int_max_str_digits()`` digits to a string, so
      ``f"{10**10000!r}"`` raises ``ValueError`` - which would replace the
      package's promised ``ConfigurationError`` with an unrelated exception
      precisely on the hostile-configuration path where the typed error matters.

    Both collapse to a placeholder that still names the type, because the type
    is what makes the message actionable.

    Scope, stated exactly rather than aspirationally: every typed rejection on
    the package's **transport boundary** renders its tail through here - the
    ``max_request_body_bytes`` cap (``views.py``), the WebSocket revalidation
    window (``consumers.py``), and the router's three factory / consumer
    rejections (``routers.py``). Those are the rejections whose argument is a
    value a hostile or fat-fingered deployment hands the package directly, which
    is where a message that raises while being formatted destroys the typed
    contract. Dozens of other ``got {...}`` tails elsewhere in the package still
    interpolate their own values; routing them is a separate change with its own
    surface and is deliberately not claimed here. A new rejection whose value came
    from outside the package belongs on
    this helper.
    """
    try:
        return f"{_safe_type_name(value)} {value!r}"
    except BaseException:
        # Deliberately NOT the ``<unprintable {T}>`` spelling its two siblings use
        # (``_safe_arg_repr`` and ``DjangoStrawberryFrameworkError.__str__``): those
        # render STANDALONE, while this one is a FRAGMENT interpolated into prose
        # ("got an unprintable Foo."). Three sites carrying two spellings is the
        # cost of that grammatical difference - do not unify them, or one of the
        # three sites reads wrongly.
        return f"an unprintable {_safe_type_name(value)}"


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
          ``search_fields``) declared before the feature that owns it has
          shipped.
        - A second ``DjangoType`` claiming ``Meta.primary`` for a model that
          already has one, or a ``primary`` flag flipped on re-register.
          Registering several types against one model is supported; only the
          ambiguity raises.
        - Several ``DjangoType`` subclasses for one model with none declared
          primary, which ``types/finalizer.py`` detects at finalization
          rather than at registration.
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
        model_label = _safe_model_label(model)
        super().__init__(
            f"Cannot classify path {_safe_arg_repr(field_path)} on model {model_label}: "
            f"segment {_safe_arg_repr(segment)} is not a traversable model-field relation.",
        )
        self.model = model
        self.field_path = field_path
        self.segment = segment

    def __reduce__(self) -> tuple[object, ...]:
        """Preserve constructor arguments and instance state across pickle roundtrips."""
        return (self.__class__, (self.model, self.field_path, self.segment), self.__dict__)


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
        terminal_label = _safe_terminal_label(terminal)
        super().__init__(
            f"Invalid lookup expression {_safe_arg_repr(lookup_expr)} for terminal "
            f"{terminal_label}: part {_safe_arg_repr(part)} is not a valid transform or lookup.",
        )
        self.terminal = terminal
        self.lookup_expr = lookup_expr
        self.part = part

    def __reduce__(self) -> tuple[object, ...]:
        """Preserve constructor arguments and instance state across pickle roundtrips."""
        return (self.__class__, (self.terminal, self.lookup_expr, self.part), self.__dict__)


class OptimizerError(DjangoStrawberryFrameworkError):
    """Raised when ``DjangoOptimizerExtension`` cannot plan a relation traversal.

    Raise sites:

        - Typed input-guard at stamp time: ``FieldMeta.from_django_field``
          rejects an input that is not a Django field descriptor (missing
          ``name`` / ``is_relation``), converting a malformed descriptor
          into a typed failure at ``DjangoType`` construction or the
          walker's unregistered fallback map-build rather than a late
          ``AttributeError`` mid-walk.
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
