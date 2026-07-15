"""Neutral write-value primitives shared by the model, form, and serializer flavors.

The flavor-neutral owner of the per-value write checks every write flavor
runs at decode time (promoted from ``mutations/resolvers.py`` so the model
mutation resolver is not the utility module for the other write flavors):

- ``unencodable_text_error`` - the invalid-Unicode storability preflight;
- ``raw_choice_value`` - choice-enum member unwrapping;
- ``coerce_relation_pk_or_none`` - raw relation-pk coercion;
- ``type_check_relation_id`` - the structural relation-id check;
- ``decode_scalar_leaf`` - the shared text-preflight + choice-unwrap compose;
- ``decode_visible_relation`` - the visibility-on-every-branch single-relation
  decode spine (type-check -> visible object -> flavor projection);
- ``decode_provided_fields`` - the kind-routed walk over a bound write input.

The set-level relation guards (visibility / existence / membership) stay in
``mutations/resolvers.py`` - they carry model-pipeline contracts, not
neutral value semantics.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from strawberry import relay

from .errors import field_error, relation_field_error
from .inputs import iter_provided_input_fields
from .querysets import coerce_field_value_or_none, visible_related_object

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from ..mutations.inputs import FieldError


def unencodable_text_error(field_name: str, value: Any) -> FieldError | None:
    r"""Reject a string input that cannot be encoded for storage (unpaired surrogate).

    A GraphQL ``String`` can carry lone UTF-16 surrogate code points (e.g. U+D800
    via a JSON ``\ud800`` escape) that are not valid Unicode scalar values and
    cannot be encoded to UTF-8. Such a value would otherwise reach a
    DB-bound operation - ``validate_unique()``'s lookup query (a unique column) or
    ``save()``'s INSERT (any text column) - where the backend raises a raw
    ``UnicodeEncodeError``. That is a ``ValueError`` the resolver does NOT map (it is
    neither the ``ValidationError`` ``full_clean`` raises nor the ``IntegrityError``
    ``save`` raises), so it escapes as a top-level GraphQL error with ``data: null``
    instead of the field-keyed envelope (feedback - surrogate text leak). Reject it
    HERE, at decode, before any DB-bound work, as a ``FieldError`` naming the
    offending input field - the same in-band envelope every other input failure
    returns - so neither the unique-field ``validate_unique`` path nor the plain
    ``save`` path can leak the raw exception. ``str.encode("utf-8")`` is the
    universal storability test: a lone surrogate fails it, while every valid scalar
    value (including an embedded ``NUL``) passes, so this rejects ONLY genuinely
    unstorable text. A non-string value (an int, a JSON dict whose own encoder
    escapes nested surrogates, a choice enum) is passed through unchanged.
    """
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            return field_error(
                field_name,
                "Text contains invalid Unicode (unpaired surrogate code points).",
                codes="invalid",
            )
    return None


def raw_choice_value(value: Any) -> Any:
    """Unwrap a choice-enum member to its raw Django choice value (spec-036 Decision 6).

    A ``choices`` column resolves to the SAME generated Strawberry ``Enum`` on the
    read ``DjangoType`` and the write input (the symmetric wire contract), so the
    client's enum value arrives here as the ENUM MEMBER (e.g.
    ``BookCirculationStatusEnum.available``), not the raw string. The member's
    ``.value`` IS the Django choice value (``convert_choices_to_enum`` maps each
    member to its choice value), so setting the member directly onto the model
    would make ``full_clean()`` reject a perfectly valid choice (the member is not
    ``== "available"``). Unwrapping to ``.value`` feeds Django the raw choice value
    it stores and validates against. A non-enum scalar is passed through unchanged;
    an explicit ``None`` (a provided null) stays ``None``.
    """
    return value.value if isinstance(value, Enum) else value


def coerce_relation_pk_or_none(related_model: type, pk: Any) -> Any:
    """Coerce a raw M2M pk through the target's pk field; ``None`` if uncoercible / out of range.

    The raw-pk M2M counterpart to ``relay.py::_coerce_pk_or_none`` (which coerces a
    ``GlobalID`` ``node_id`` through the resolved Strawberry type's id field). A
    raw-pk relation has no Relay-Node type and so no ``resolve_id_attr`` seam: the
    existence query filters on ``pk__in`` directly, so coercion is against
    ``related_model._meta.pk`` via the shared
    ``querysets.py::coerce_field_value_or_none`` primitive - the same
    ``to_python``-then-``run_validators`` mechanics the GlobalID path uses, so an
    out-of-range pk (beyond the backend's signed-64-bit column range) is rejected
    as a ``ValidationError`` here rather than reaching ``pk__in`` and raising a raw
    backend ``OverflowError`` (``Python int too large to convert to SQLite
    INTEGER``). An uncoercible / out-of-range pk is treated as "identifies no
    row" - excluded from the existence query and so absent from the visible set,
    which makes it the same not-found ``relation_field_error`` as a genuinely
    missing pk, never a backend crash (feedback - relation huge-pk crash).
    """
    return coerce_field_value_or_none(related_model._meta.pk, pk)


def type_check_relation_id(
    value: Any,
    *,
    graphql_name: str,
    related_model: type,
) -> tuple[Any, FieldError | None]:
    """Type-check + coerce ONE relation id to a pk WITHOUT a DB fetch (spec-039 M3).

    The "GlobalID -> ``decode_model_global_id`` (non-``OK`` -> uniform relation
    error) | raw pk -> ``coerce_relation_pk_or_none`` (``None`` -> uniform relation
    error)" two-branch structural check the three write flavors share. Promoted here
    (from the serializer's cleanly-factored ``_type_check_relation_id``) so the
    single definition of "what counts as a well-formed relation id" is shared: the
    serializer single/multi decoders call it, and the form single decoder calls it
    (keeping only its ``empty_values`` pass-through + ``to_field_name`` reduction on
    top). Neither branch touches the DB - visibility is confirmed separately by the
    caller.

    The model batched decoder (``_decode_relation_id_set``) deliberately does NOT use
    this: its raw-pk half is a set-level all-or-nothing visibility / existence check
    (``_raw_pk_relation_error``), a genuinely different contract; only its GlobalID
    half mirrors the check here. A ``relay.GlobalID`` is decoded against the target
    model (a non-``OK`` status is the uniform ``relation_field_error``); a raw pk is
    coerced through the target pk field (``None`` -> the uniform error).

    The ``decode_model_global_id`` / ``GlobalIDDecode`` import is function-local:
    the package's ``relay`` module imports ``utils.querysets`` at module level, so
    a module-level import here would risk an import cycle through the utils
    package.
    """
    if isinstance(value, relay.GlobalID):
        from ..relay import GlobalIDDecode, decode_model_global_id

        result = decode_model_global_id(value, related_model)
        if result.status is not GlobalIDDecode.OK:
            return None, relation_field_error(graphql_name)
        return result.pk, None
    pk = coerce_relation_pk_or_none(related_model, value)
    if pk is None:
        return None, relation_field_error(graphql_name)
    return pk, None


def decode_scalar_leaf(graphql_name: str, value: Any) -> tuple[Any, FieldError | None]:
    """Run the shared scalar leaf decode: text preflight, then choice unwrap (DRY review A6).

    The two-step compose every write flavor runs on a provided scalar value -
    ``unencodable_text_error`` (an unstorable lone surrogate is a field-keyed
    ``FieldError`` at decode, never a raw backend ``UnicodeEncodeError`` at
    ``save()``) then ``raw_choice_value`` (a choice-enum member unwrapped to the
    raw Django choice value). The primitives were already shared; this owns the
    compose so a fourth flavor cannot mis-order it. Returns ``(decoded, None)``
    on success or ``(None, FieldError)``. Flavor-specific scalar steps (the model
    path's explicit-null rejection and naive-datetime coercion) stay at the call
    site, composed around this leaf.
    """
    error = unencodable_text_error(graphql_name, value)
    if error is not None:
        return None, error
    return raw_choice_value(value), None


def decode_visible_relation(
    value: Any,
    *,
    graphql_name: str,
    related_model: type,
    info: Any,
    async_recourse: str,
    skip: Callable[[Any], bool],
    project: Callable[[Any], Any],
) -> tuple[Any, FieldError | None]:
    """Decode ONE relation id to its visible, flavor-projected value (DRY review A1).

    The single-relation decode spine the form and serializer flavors share - and
    the owner of the **cross-flavor security invariant** that a writer must never
    attach a row it cannot see:

    (i) ``skip(value)`` short-circuits a clear / no-value (the form's
    ``empty_values``, the serializer's explicit ``None``) UNCHANGED, so the bound
    form / serializer's own validation decides required-ness; (ii) the structural
    type-check + pk coercion is ``type_check_relation_id`` (a non-``OK``
    ``GlobalID`` / an uncoercible raw pk is the uniform field-keyed
    ``FieldError``); (iii) the type-checked pk is resolved to the VISIBLE object
    via ``visible_related_object`` - a hidden / missing row is the SAME
    field-keyed ``FieldError`` (hidden and missing indistinguishable, no
    existence leak); (iv) ``project(obj)`` reduces the visible object to the
    flavor's bound-data value (the form's ``to_field_name`` key, the serializer's
    ``obj.pk``).

    Returns ``(projected, None)`` on success or ``(None, FieldError)``. The
    MULTI decoders deliberately keep their query strategy at each flavor (the
    form maps this per element - it needs the object for ``to_field_name``; the
    serializer batches one ``pk__in`` visibility query) - only the per-id spine
    is promoted.
    """
    if skip(value):
        return value, None
    pk, error = type_check_relation_id(
        value,
        graphql_name=graphql_name,
        related_model=related_model,
    )
    if error is not None:
        return None, error
    obj = visible_related_object(related_model, pk, info, async_recourse)
    if obj is None:
        return None, relation_field_error(graphql_name)
    return project(obj), None


def decode_provided_fields(
    specs: list,
    data: Any,
    *,
    handlers: dict[str, Callable[[Any, Any], FieldError | None]],
    scalar_handler: Callable[[Any, Any], FieldError | None],
) -> FieldError | None:
    """Route each provided input field by ``spec.kind`` through a handler map (DRY review A2).

    The kind-dispatch decode loop the form and serializer flavors share: build
    the ``{spec.input_attr: spec}`` reverse map, walk the PROVIDED input fields
    (``UNSET`` stripped - single-sited in ``iter_provided_input_fields``), and
    hand each ``(spec, value)`` to the flavor's handler for ``spec.kind``
    (falling back to ``scalar_handler`` for the scalar leaf). Each handler owns
    its flavor's destination policy (the form splits ``provided_files`` for
    Django's ``files=``; the serializer routes everything into ``data``,
    including its ``NESTED_*`` recursion) by closing over the destination
    dict(s), and returns a ``FieldError`` to short-circuit or ``None`` to
    continue. Returns the first handler ``FieldError`` or ``None``.

    The model flavor's ``mutations/resolvers.py::_decode_relations`` is a
    near-parallel with a genuinely different key space (model attrs, the batched
    id-set contract) and stays put (DRY review F5).
    """
    spec_by_attr = {spec.input_attr: spec for spec in specs}
    for python_name, value, _field in iter_provided_input_fields(data):
        spec = spec_by_attr[python_name]
        error = handlers.get(spec.kind, scalar_handler)(spec, value)
        if error is not None:
            return error
    return None
