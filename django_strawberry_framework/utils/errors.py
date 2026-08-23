"""Neutral ``FieldError`` / write-error constructors shared by every write flavor.

The flavor-neutral owner of the write-error envelope's leaf construction
(promoted from ``mutations/resolvers.py`` so the model mutation resolver is
not the utility module for the form, serializer, auth, and future write
flavors):

- ``field_error`` - the single ``FieldError`` leaf constructor;
- ``relation_field_error`` - the uniform relation-decode error;
- ``validation_error_to_field_errors`` - the Django ``ValidationError`` mapper;
- ``integrity_error_field_errors`` - the save-time ``IntegrityError`` envelope;
- ``join_error_path`` - dotted GraphQL error-path joining for nested
  flatteners.

Layering: ``FieldError`` and ``NON_FIELD_ERROR_KEY`` live in
``mutations/inputs.py`` (the single source); utils must not import the
mutations package at module import time, so each constructor imports them
function-locally (the repo's established cross-package seam, see
``auth/*.py``).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.utils.functional import Promise

from ..exceptions import _safe_type_name

if TYPE_CHECKING:  # pragma: no cover
    from ..mutations.inputs import FieldError


def field_error(path: str, messages: Any, *, codes: Any = None) -> FieldError:
    """Build ONE ``FieldError`` leaf for the shared envelope.

    The single leaf constructor BOTH the flat Django mapper
    (``validation_error_to_field_errors``) and the recursive DRF serializer
    flattener (``rest_framework/resolvers.py::serializer_errors_to_field_errors``)
    call, so the ``"__all__"`` sentinel + the message-container coercion + the
    structured ``path`` / ``codes`` derivation cannot drift between the two flatteners
    (nor across the three write flavors). An empty ``path`` (a model-wide / non-field
    error) is normalized to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to Django's
    ``"__all__"`` in ``mutations/inputs.py`` - the single source). ``messages`` is
    coerced to a ``list[str]``: a bare string becomes a one-element list, any other
    iterable (a DRF ``ErrorDetail`` list, a tuple) is materialized as a list.

    **Structured ``path``:** the dotted ``path`` string is split into segments
    (``items.0.name`` -> ``["items", "0", "name"]``); an empty ``path`` (the root non-field
    error) yields ``[]`` while ``field`` is the ``"__all__"`` sentinel - the documented
    root rule. **Structured ``codes``:** the caller passes the DRF
    ``ErrorDetail.code``s / Django ``ValidationError.code``s (or a framework code); ``None``
    yields ``[]``.
    """
    from ..mutations.inputs import NON_FIELD_ERROR_KEY, FieldError

    normalized_path = _safe_text(path, fallback="") if path is not None else ""
    key = normalized_path if normalized_path else NON_FIELD_ERROR_KEY
    # Root rule: a model-wide / non-field error (an empty path, or the bare
    # ``"__all__"`` sentinel as the WHOLE path - the DRF flattener joins the top-level
    # non-field bucket to exactly that) carries an EMPTY ``path``, while ``field`` stays
    # ``"__all__"``; a NESTED non-field error (``items.0.__all__``) keeps its segments. So
    # the model + serializer flavors agree on the root-non-field shape.
    segments = (
        []
        if not normalized_path or normalized_path == NON_FIELD_ERROR_KEY
        else normalized_path.split(
            ".",
        )
    )
    return FieldError(
        field=key,
        messages=_str_list(messages),
        codes=_str_list(codes) if codes is not None else [],
        path=segments,
    )


def _str_list(value: Any) -> list[str]:
    """Coerce a bare string or an iterable into a ``list[str]``.

    The one body behind ``field_error``'s ``messages`` AND ``codes`` coercion
    (the rule the DRF ``ErrorDetail`` flattener depends on): a bare string
    becomes a one-element list (never iterated char-by-char); any other iterable
    (a DRF ``ErrorDetail`` list, a tuple) is materialized with each element
    stringified.
    """
    try:
        is_str = isinstance(value, (str, Promise))
    except BaseException:
        is_str = False
    if is_str:
        return [_safe_text(value)]
    try:
        is_iter = isinstance(
            value,
            (
                list,
                tuple,
                set,
                frozenset,
                Iterable,
            ),
        ) and not isinstance(
            value,
            (
                bytes,
                bytearray,
                memoryview,
                Promise,
            ),
        )
    except BaseException:
        is_iter = False
    if not is_iter:
        return [_safe_text(value)]
    try:
        items = list(value)
    except BaseException:
        return [_unprintable(value)]
    return [_safe_text(item) for item in items]


def _safe_text(value: Any, *, fallback: str = "") -> str:
    """Render one error value without dispatching a hostile string dunder.

    Validation messages and field names are normally Django-owned strings, but
    ``ValidationError`` also accepts consumer objects and ``str`` subclasses.
    Error normalization is the last step before a mutation envelope reaches
    GraphQL, so a failing ``__str__`` must not replace that expected envelope
    with a raw exception.  Calling ``str.__str__`` directly also normalizes a
    string subclass whose overridden ``__str__`` / ``__repr__`` is hostile.
    """
    try:
        rendered = str.__str__(value) if isinstance(value, str) else str(value)
    except BaseException:
        return _unprintable(value)
    return rendered or fallback


def _unprintable(value: Any) -> str:
    """Return a stable placeholder for an error value that cannot be rendered."""
    return f"<unprintable {_safe_type_name(value)}>"


def _validation_messages(error: Any) -> list[Any]:
    """Read one Django validation leaf's messages without trusting its metadata."""
    try:
        msgs = error.messages
        if isinstance(
            msgs,
            (
                str,
                bytes,
                bytearray,
                memoryview,
                Promise,
            ),
        ):
            return [msgs]
        return list(msgs)
    except BaseException:
        try:
            msg = error.message
            if isinstance(
                msg,
                (
                    list,
                    tuple,
                    set,
                    frozenset,
                ),
            ):
                return list(msg)
            return [msg]
        except BaseException:
            return [error]


def _validation_code(leaf: Any) -> Any:
    """Read one Django validation leaf's code, dropping hostile or empty values."""
    try:
        code = leaf.code
        return code if code else None
    except BaseException:
        return None


def _validation_codes(error: Any) -> list[Any]:
    """Read all codes from one Django validation error leaf."""
    try:
        error_list = getattr(error, "error_list", None)
        if error_list is not None:
            leaves = (
                (error_list,)
                if isinstance(
                    error_list,
                    (
                        str,
                        bytes,
                        bytearray,
                        memoryview,
                        Promise,
                    ),
                )
                else tuple(error_list)
            )
        else:
            leaves = (error,)
    except BaseException:
        leaves = (error,)
    return [code for leaf in leaves if (code := _validation_code(leaf)) is not None]


def _empty_validation_error(path: str = "") -> FieldError:
    """Build the fail-closed leaf for a validation failure carrying no details."""
    return field_error(
        path,
        "Validation failed without error details.",
        codes="invalid",
    )


def _error_dict_entry(item: Any) -> tuple[Any, Any] | None:
    """Unpack one ``ValidationError.error_dict`` item without trusting its shape."""
    try:
        field_name, field_errors = item
    except BaseException:
        return None
    return field_name, field_errors


def relation_field_error(graphql_name: str) -> FieldError:
    """Build the uniform invalid / hidden / wrong-model relation ``FieldError`` (spec-039 integration).

    The single leaf constructor for the relation-decode error all three write
    flavors raise - the ``036`` model path (``decode_visible_relation_ids``),
    the ``038`` form decoder, and the ``039`` serializer decoder all call this
    DIRECTLY (spec-039 folded away the former per-flavor ``_relation_error`` /
    ``_relation_field_error`` aliases). A wrong-model, hidden, missing, or
    uncoercible id all collapse to this one field-keyed shape (no existence
    leak), keyed to the GraphQL wire name the client sent (``categoryId``). Siblings
    the ``field_error`` leaf ctor above so the ``"Invalid id for relation ..."`` message
    + leaf construction are single
    sourced across every flavor.
    """
    name = _safe_text(graphql_name)
    return field_error(name, f"Invalid id for relation {name!r}.", codes="invalid")


def validation_error_to_field_errors(exc: ValidationError) -> list[FieldError]:
    """Map a Django ``ValidationError`` to the ``FieldError`` envelope (spec-036 Decision 7).

    Uses ``exc.error_dict`` when present (per-field), keying the model's
    ``NON_FIELD_ERRORS`` bucket to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to
    ``"__all__"`` in ``mutations/inputs.py`` - the single source) so a
    multi-field-constraint error surfaces under ``"__all__"``. Falls back to
    ``exc.messages`` under the sentinel for a non-dict ``ValidationError``. The
    single source for both the ``full_clean()`` failure and the
    ``IntegrityError``-race fallback mapping. Both leaves are built through the
    shared ``field_error`` leaf ctor so the sentinel + message coercion stay
    single-sited with the recursive DRF flattener.
    """
    try:
        error_dict = exc.error_dict
    except BaseException:
        error_dict = None
    if error_dict is not None:
        errors: list[FieldError] = []
        try:
            error_items = tuple(error_dict.items())
        except BaseException:
            error_items = None
        # An unreadable ``items()`` leaves the dict branch entirely and falls
        # through to the ``error_list`` / ``messages`` fallback below.
        if error_items is not None:
            for item in error_items:
                unpacked = _error_dict_entry(item)
                if unpacked is None:
                    errors.append(
                        field_error(
                            "",
                            "Validation details could not be normalized.",
                            codes="invalid",
                        ),
                    )
                    continue
                field_name, field_errors = unpacked
                normalized_name = _safe_text(field_name)
                path = "" if normalized_name == NON_FIELD_ERRORS else normalized_name
                if isinstance(
                    field_errors,
                    (
                        str,
                        bytes,
                        bytearray,
                        memoryview,
                        Promise,
                    ),
                ):
                    field_error_items: tuple[Any, ...] = (field_errors,)
                else:
                    try:
                        field_error_items = tuple(field_errors)
                    except BaseException:
                        field_error_items = (field_errors,)
                messages: list[Any] = []
                for error in field_error_items:
                    messages.extend(_validation_messages(error))
                # Preserve each leaf Django ``ValidationError.code`` alongside the
                # message (``error.error_list`` is the flattened leaf list ``error.messages``
                # reads; a ``None`` code is dropped).
                codes = [code for error in field_error_items for code in _validation_codes(error)]
                errors.append(
                    field_error(path, messages, codes=codes)
                    if messages
                    else _empty_validation_error(path),
                )
            if errors:
                return errors
    try:
        error_list = getattr(exc, "error_list", None)
        if error_list is not None:
            leaves = (
                (error_list,)
                if isinstance(
                    error_list,
                    (
                        str,
                        bytes,
                        bytearray,
                        memoryview,
                        Promise,
                    ),
                )
                else tuple(error_list)
            )
        else:
            leaves = (exc,)
    except BaseException:
        leaves = (exc,)
    codes = [code for leaf in leaves if (code := _validation_code(leaf)) is not None]
    messages = _validation_messages(exc)
    return [field_error("", messages, codes=codes) if messages else _empty_validation_error()]


def integrity_error_field_errors() -> list[FieldError]:
    """Map a save-time ``IntegrityError`` to the ``"__all__"`` envelope.

    The residual after ``full_clean()`` / serializer ``is_valid()``: a constraint
    violation that beat validation (a uniqueness race, a ``NOT NULL`` / FK /
    ``CHECK`` the flavor did not catch on the normal path). The catch is
    ``except IntegrityError`` (broad), so the message is the honest superset
    "A database constraint was violated." rather than over-claiming uniqueness.
    Keys to the ``"__all__"`` sentinel - ``save()``'s ``IntegrityError`` carries
    no reliable cross-backend field mapping. The model, form, and serializer
    write paths all return this same leaf (via ``save_or_field_errors`` or the
    serializer's three-``except`` save mapping).
    """
    return [field_error("", "A database constraint was violated.", codes="constraint")]


def join_error_path(prefix: str, segment: str) -> str:
    """Join a dotted-path prefix with a child segment (``items`` + ``0`` -> ``items.0``).

    The dotted GraphQL error-path joining shared by nested write-error
    flatteners: an empty ``prefix`` (the root level) yields the bare segment,
    so a root non-field key stays ``__all__`` while a nested one becomes
    ``items.0.__all__`` (the root-vs-nested ``__all__`` distinction itself
    stays with each flattener's key handling).
    """
    normalized_prefix = _safe_text(prefix, fallback="") if prefix is not None else ""
    normalized_segment = _safe_text(segment)
    return f"{normalized_prefix}.{normalized_segment}" if normalized_prefix else normalized_segment
