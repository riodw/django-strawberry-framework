"""Neutral ``FieldError`` / write-error constructors shared by every write flavor.

The flavor-neutral owner of the write-error envelope's leaf construction
(promoted from ``mutations/resolvers.py`` so the model mutation resolver is
not the utility module for the form, serializer, auth, and future write
flavors):

- ``field_error`` - the single ``FieldError`` leaf constructor;
- ``relation_field_error`` - the uniform relation-decode error;
- ``validation_error_to_field_errors`` - the Django ``ValidationError`` mapper;
- ``join_error_path`` - dotted GraphQL error-path joining for nested
  flatteners.

Layering: ``FieldError`` and ``NON_FIELD_ERROR_KEY`` live in
``mutations/inputs.py`` (the AR-M3 single source); utils must not import the
mutations package at module import time, so each constructor imports them
function-locally (the repo's established cross-package seam, see
``auth/*.py``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

if TYPE_CHECKING:  # pragma: no cover
    from ..mutations.inputs import FieldError


def field_error(path: str, messages: Any, *, codes: Any = None) -> FieldError:
    """Build ONE ``FieldError`` leaf for the shared envelope (spec-039 P2.4 / rev6 #4 / #13).

    The single leaf constructor BOTH the flat Django mapper
    (``validation_error_to_field_errors``) and the recursive DRF serializer
    flattener (``rest_framework/resolvers.py::serializer_errors_to_field_errors``)
    call, so the ``"__all__"`` sentinel + the message-container coercion + the
    structured ``path`` / ``codes`` derivation cannot drift between the two flatteners
    (nor across the three write flavors). An empty ``path`` (a model-wide / non-field
    error) is normalized to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to Django's
    ``"__all__"`` in ``mutations/inputs.py`` - AR-M3, single source). ``messages`` is
    coerced to a ``list[str]``: a bare string becomes a one-element list, any other
    iterable (a DRF ``ErrorDetail`` list, a tuple) is materialized as a list.

    **Structured ``path`` (rev6 #13):** the dotted ``path`` string is split into segments
    (``items.0.name`` -> ``["items", "0", "name"]``); an empty ``path`` (the root non-field
    error) yields ``[]`` while ``field`` is the ``"__all__"`` sentinel - the documented
    root rule. **Structured ``codes`` (rev6 #4):** the caller passes the DRF
    ``ErrorDetail.code``s / Django ``ValidationError.code``s (or a framework code); ``None``
    yields ``[]``.
    """
    from ..mutations.inputs import NON_FIELD_ERROR_KEY, FieldError

    key = path if path else NON_FIELD_ERROR_KEY
    # rev6 #13 root rule: a model-wide / non-field error (an empty path, or the bare
    # ``"__all__"`` sentinel as the WHOLE path - the DRF flattener joins the top-level
    # non-field bucket to exactly that) carries an EMPTY ``path``, while ``field`` stays
    # ``"__all__"``; a NESTED non-field error (``items.0.__all__``) keeps its segments. So
    # the model + serializer flavors agree on the root-non-field shape.
    segments = [] if not path or path == NON_FIELD_ERROR_KEY else path.split(".")
    return FieldError(
        field=key,
        messages=_str_list(messages),
        codes=_str_list(codes) if codes is not None else [],
        path=segments,
    )


def _str_list(value: Any) -> list[str]:
    """Coerce a bare string or an iterable into a ``list[str]`` (DRY review C1).

    The one body behind ``field_error``'s ``messages`` AND ``codes`` coercion
    (the rule the DRF ``ErrorDetail`` flattener depends on): a bare string
    becomes a one-element list (never iterated char-by-char); any other iterable
    (a DRF ``ErrorDetail`` list, a tuple) is materialized with each element
    stringified.
    """
    return [value] if isinstance(value, str) else [str(item) for item in value]


def relation_field_error(graphql_name: str) -> FieldError:
    """Build the uniform invalid / hidden / wrong-model relation ``FieldError`` (spec-039 integration).

    The single leaf constructor for the relation-decode error all three write
    flavors raise - the ``036`` model path (``_decode_relation_id_set`` /
    ``_relation_membership_error``), the ``038`` form decoder, and the ``039``
    serializer decoder all call this DIRECTLY (spec-039 Mn1 folded away the former
    per-flavor ``_relation_error`` / ``_relation_field_error`` aliases). A
    wrong-model, hidden, missing, or uncoercible id all collapse to this one
    field-keyed shape (no existence leak), keyed to the GraphQL wire name the
    client sent (``categoryId``). Siblings the ``field_error`` leaf ctor above so
    the ``"Invalid id for relation ..."`` message + leaf construction are single
    sourced across every flavor (AR-H4).
    """
    return field_error(graphql_name, f"Invalid id for relation {graphql_name!r}.", codes="invalid")


def validation_error_to_field_errors(exc: ValidationError) -> list[FieldError]:
    """Map a Django ``ValidationError`` to the ``FieldError`` envelope (spec-036 Decision 7 / AR-M3).

    Uses ``exc.error_dict`` when present (per-field), keying the model's
    ``NON_FIELD_ERRORS`` bucket to the ``NON_FIELD_ERROR_KEY`` sentinel (pinned to
    ``"__all__"`` in ``mutations/inputs.py`` - AR-M3, single source) so a
    multi-field-constraint error surfaces under ``"__all__"``. Falls back to
    ``exc.messages`` under the sentinel for a non-dict ``ValidationError``. The
    single source for both the ``full_clean()`` failure and the
    ``IntegrityError``-race fallback mapping. Both leaves are built through the
    shared ``field_error`` leaf ctor (P2.4) so the sentinel + message coercion stay
    single-sited with the recursive DRF flattener.
    """
    if hasattr(exc, "error_dict"):
        errors: list[FieldError] = []
        for field_name, field_errors in exc.error_dict.items():
            path = "" if field_name == NON_FIELD_ERRORS else field_name
            messages = [message for error in field_errors for message in error.messages]
            # rev6 #4: preserve each leaf Django ``ValidationError.code`` alongside the
            # message (``error.error_list`` is the flattened leaf list ``error.messages``
            # reads; a ``None`` code is dropped).
            codes = [leaf.code for error in field_errors for leaf in error.error_list if leaf.code]
            errors.append(field_error(path, messages, codes=codes))
        return errors
    codes = [leaf.code for leaf in exc.error_list if leaf.code]
    return [field_error("", list(exc.messages), codes=codes)]


def join_error_path(prefix: str, segment: str) -> str:
    """Join a dotted-path prefix with a child segment (``items`` + ``0`` -> ``items.0``).

    The dotted GraphQL error-path joining shared by nested write-error
    flatteners: an empty ``prefix`` (the root level) yields the bare segment,
    so a root non-field key stays ``__all__`` while a nested one becomes
    ``items.0.__all__`` (the root-vs-nested ``__all__`` distinction itself
    stays with each flattener's key handling).
    """
    return f"{prefix}.{segment}" if prefix else segment
