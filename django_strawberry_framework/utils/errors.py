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
  flatteners;
- ``null_field_error`` / ``empty_validation_error`` - the two leaves whose
  message + code pair was being re-typed by consumers of the module;
- ``FIELD_ERROR_CODE_*`` - the ``FieldError.codes`` vocabulary, which is a
  public wire contract that previously existed only as the union of string
  literals at 19 raise sites;
- ``coded_error_extensions`` + ``*_ERROR_CODE`` - the ``extensions={"code": ...}``
  shape and code vocabulary every framework ``GraphQLError`` carries.

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

from ..exceptions import _safe_text, _unprintable

if TYPE_CHECKING:  # pragma: no cover
    from ..mutations.inputs import FieldError

__all__ = [
    "FIELD_ERROR_CODE_CONFLICT",
    "FIELD_ERROR_CODE_CONSTRAINT",
    "FIELD_ERROR_CODE_INVALID",
    "FIELD_ERROR_CODE_NOT_FOUND",
    "FIELD_ERROR_CODE_NULL",
    "FIELD_ERROR_CODE_PROTECTED",
    "FIELD_ERROR_CODE_TRUNCATED",
    "FILTER_INVALID_ERROR_CODE",
    "GLOBALID_INVALID_ERROR_CODE",
    "GLOBALID_UNVALIDATABLE_ERROR_CODE",
    "coded_error_extensions",
    "empty_validation_error",
    "field_error",
    "integrity_error_field_errors",
    "join_error_path",
    "null_field_error",
    "relation_field_error",
    "validation_error_to_field_errors",
]

# The text atoms: values that ARE a message rather than a container of messages.
# Spelled once because missing a site when the set grows is not a cosmetic slip -
# it makes a message iterate character-by-character into per-character
# ``FieldError`` leaves, the exact failure ``_str_list`` exists to prevent.
# The write path has its own, deliberately different atom set (it also excludes
# ``Mapping``): see ``write_values.py::RELATION_ID_ATOM_TYPES``.
_TEXT_ATOM_TYPES = (
    str,
    bytes,
    bytearray,
    memoryview,
    Promise,
)

# ---------------------------------------------------------------------------
# ``FieldError.codes`` vocabulary
# ---------------------------------------------------------------------------
# The codes the framework itself emits on the write envelope. This is derived
# knowledge with no other home: the vocabulary is what a client branches on, yet
# it used to exist only as the union of string literals across three subsystems.
#
# Framework ``"invalid"`` deliberately COLLIDES with Django's and DRF's own
# ``"invalid"`` on the wire - a client cannot tell a framework relation-decode
# rejection from a Django field-validation one by code alone, and that is the
# established shape, not an oversight to fix here.
#
# These are constants, not an ``Enum``, and ``codes=`` arguments are NOT
# validated against them: ``FieldError.codes`` is ``list[str]`` on the wire and
# Django / DRF codes flow through the same parameter, so the vocabulary must
# stay open at the constructor.
FIELD_ERROR_CODE_INVALID = "invalid"
FIELD_ERROR_CODE_NULL = "null"
FIELD_ERROR_CODE_CONSTRAINT = "constraint"
FIELD_ERROR_CODE_NOT_FOUND = "not_found"
FIELD_ERROR_CODE_PROTECTED = "protected"
FIELD_ERROR_CODE_CONFLICT = "conflict"
FIELD_ERROR_CODE_TRUNCATED = "truncated"

# ---------------------------------------------------------------------------
# Coded ``GraphQLError`` extensions
# ---------------------------------------------------------------------------
# The OTHER error vocabulary: the ``extensions={"code": ...}`` payload a
# framework ``GraphQLError`` carries so a client can act on a rejection without
# parsing prose. ``resource_policy.py::RESOURCE_LIMIT_ERROR_CODE`` is the
# established public spelling and stays exported from there (it is already in
# the package root's ``__all__``); the codes below had no owner at all and were
# re-typed as literals at each raise site, with the convention itself
# transmitted only through docstrings.
GLOBALID_INVALID_ERROR_CODE = "GLOBALID_INVALID"
GLOBALID_UNVALIDATABLE_ERROR_CODE = "GLOBALID_UNVALIDATABLE"
FILTER_INVALID_ERROR_CODE = "FILTER_INVALID"


def coded_error_extensions(code: str, **detail: Any) -> dict[str, Any]:
    """Build the ``extensions`` mapping for a coded framework ``GraphQLError``.

    One shape for every coded error the framework raises: a ``"code"`` key
    naming the machine-readable rejection, plus whatever structured detail the
    raise site wants a client to be able to act on without parsing prose
    (``ResourceLimitExceeded``'s ``bound`` / ``limit`` / ``charged``, the
    filterset's ``errors`` payload). Keyword names become extension keys
    verbatim.

    Layering: this owns the SHAPE, never the vocabulary of any one subsystem -
    ``errors.py`` sits below ``filters/`` and ``relay.py`` and must never import
    from them. Codes flow downward: a subsystem's code constant either lives
    here (the three below) or stays at its own owner and is passed in.
    """
    return {"code": code, **detail}


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
    # A deliberate SUBSET of ``_TEXT_ATOM_TYPES``, not a missed site: this asks
    # "is this already text?" (the one-element-list path), while the exclusion
    # below asks "is this an atom rather than a container?". The byte-ish atoms
    # are excluded from iteration but are not stringified by this first branch.
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
        ) and not isinstance(value, _TEXT_ATOM_TYPES)
    except BaseException:
        is_iter = False
    if not is_iter:
        return [_safe_text(value)]
    try:
        items = list(value)
    except BaseException:
        return [_unprintable(value)]
    return [_safe_text(item) for item in items]


def _validation_messages(error: Any) -> list[Any]:
    """Read one Django validation leaf's messages without trusting its metadata."""
    try:
        msgs = error.messages
        if isinstance(msgs, _TEXT_ATOM_TYPES):
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


def _validation_leaves(error: Any) -> tuple[Any, ...]:
    """Flatten one Django validation error into its leaf errors.

    ``ValidationError.error_list`` is the flattened leaf list ``.messages``
    reads. A hostile or absent ``error_list``, and a text atom planted in the
    slot (which would otherwise be iterated character-by-character), both fall
    back to treating the error itself as the single leaf.
    """
    try:
        error_list = getattr(error, "error_list", None)
        if error_list is None:
            return (error,)
        if isinstance(error_list, _TEXT_ATOM_TYPES):
            return (error_list,)
        return tuple(error_list)
    except BaseException:
        return (error,)


def _validation_codes(error: Any) -> list[Any]:
    """Read all codes from one Django validation error leaf."""
    leaves = _validation_leaves(error)
    return [code for leaf in leaves if (code := _validation_code(leaf)) is not None]


def empty_validation_error(path: str = "") -> FieldError:
    """Build the fail-closed leaf for a validation failure carrying no details.

    Public because the DRF flattener needs it: a serializer whose ``is_valid()``
    fails with an empty (or unreadable) error payload still owes the envelope a
    leaf, and ``rest_framework/resolvers.py`` was hand-building this exact
    message + code pair at two sites purely because the name started with an
    underscore. The module docstring's claim that the DRF flattener calls the
    single leaf constructor is only true once this is reachable.
    """
    return field_error(
        path,
        "Validation failed without error details.",
        codes=FIELD_ERROR_CODE_INVALID,
    )


def null_field_error(path: str) -> FieldError:
    """Build the uniform "required field was sent as null" ``FieldError``.

    Siblings :func:`relation_field_error`: one message + code pair for the
    rejection every write flavor makes when a non-nullable field arrives
    explicitly null. The auth flavor reached this leaf through
    ``mutations/resolvers.py`` - importing a write-envelope leaf from the MODEL
    mutation resolver is exactly the layering the promotion of these
    constructors into ``utils/errors.py`` exists to undo.

    The M2M "send an empty list to clear it" rejection is a different
    condition with its own message and is deliberately NOT folded in here.
    """
    return field_error(path, "This field cannot be null.", codes=FIELD_ERROR_CODE_NULL)


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
    return field_error(
        name,
        f"Invalid id for relation {name!r}.",
        codes=FIELD_ERROR_CODE_INVALID,
    )


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
                            codes=FIELD_ERROR_CODE_INVALID,
                        ),
                    )
                    continue
                field_name, field_errors = unpacked
                normalized_name = _safe_text(field_name)
                path = "" if normalized_name == NON_FIELD_ERRORS else normalized_name
                if isinstance(field_errors, _TEXT_ATOM_TYPES):
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
                    else empty_validation_error(path),
                )
            if errors:
                return errors
    leaves = _validation_leaves(exc)
    codes = [code for leaf in leaves if (code := _validation_code(leaf)) is not None]
    messages = _validation_messages(exc)
    return [field_error("", messages, codes=codes) if messages else empty_validation_error()]


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
    return [
        field_error(
            "",
            "A database constraint was violated.",
            codes=FIELD_ERROR_CODE_CONSTRAINT,
        ),
    ]


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
