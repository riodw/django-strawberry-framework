"""The sync + async serializer-mutation resolver pipeline (spec-039 Slice 3).

The DRF-serializer write runtime, the third sibling of ``mutations/resolvers.py``
(the ``036`` model pipeline) and ``forms/resolvers.py`` (the ``038`` form
pipeline). The pipeline is (spec-039 Decision 8):

    (update) locate -> authorize -> decode -> construct -> validate
            -> write -> re-fetch -> payload

**Authorize runs BEFORE the relation decode** (the ``036`` / ``038`` security
invariant): the decode issues visibility-scoped ``get_queryset`` queries, so
running it pre-auth would let an unauthorized caller probe related-object
visibility by id (a write-auth denial ``GraphQLError`` vs an in-band relation
``FieldError`` is an observable distinction). The ``transaction.atomic()``
boundary + the locate preamble + the authorize-before-decode ordering + the
optimizer re-fetch tail are NOT re-hand-rolled here: they are single-sited in the
promoted ``mutations/resolvers.py::run_write_pipeline_sync`` skeleton (spec-039
P1.5), and this flavor supplies only the serializer ``decode_step`` /
``write_step`` callbacks.

The serializer-specific invariants this module owns:

- **The decode produces a SERIALIZER-FIELD-keyed ``provided_data``** (Decision 8
  step 1). DRF serializers are keyed by DECLARED field name and read uploads from
  ``data`` like any other value (the deliberate contrast with Django forms, which
  split ``files=``). The Slice-1 reverse map
  (``mutation_cls._input_field_specs``, a list of
  ``utils/inputs.py::InputFieldSpec``) routes each provided input attr to its
  serializer field name (``spec.target_name``) + decode ``kind`` (``SCALAR`` /
  ``RELATION_SINGLE`` / ``RELATION_MULTI`` / ``FILE``).

- **The dedicated serializer relation decoder mirrors the ``038`` form decoder**
  (serializer-field-keyed, NOT the model-attr-keyed ``036``
  ``_decode_relation_id_set``). Each relation id - a ``relay.GlobalID`` *or* a raw
  pk - is type-checked against the relation's **target model**, which is recorded on
  the bind-stashed reverse map (``InputFieldSpec.related_model``, resolved once at
  build from the backing FK via the serializer field's ``source``, or
  ``field.queryset.model`` for a serializer-only relation - spec-039 H4, so the
  query path never re-discovers the serializer field set), then **resolved to the
  visible object through
  the related primary ``DjangoType.get_queryset``** via the promoted
  ``utils/querysets.py::visible_related_object`` (P1.1 - the SAME object-returning
  visibility query the form decoder re-keys over), reduced to the pk a
  ``PrimaryKeyRelatedField`` expects. A hidden / wrong-model / uncoercible id is a
  field-keyed ``FieldError`` keyed to ``spec.graphql_name`` (the GraphQL wire name
  the client sent, e.g. ``categoryId``). The generated input field exposes exactly
  ONE strategy-dependent shape (Decision 7 - a ``GlobalID`` for a Relay target,
  else the raw-pk scalar); the shared decode helper accepts BOTH only because
  package tests drive the raw-pk / non-Relay branch by direct call (M1).

- **A relation ``GlobalID`` is decoded against the target type's RECORDED
  ``effective_globalid_strategy``** via ``decode_model_global_id`` (which takes the
  expected model and reads the recorded state), NOT a live settings read / a
  strategy re-validation on the query path (the config-assessment grep-guard,
  Decision; the strategy is resolved once at finalization, never re-read per
  request).

- **The serializer is constructed via the overridable ``get_serializer_kwargs``
  hook + the framework merge** (Decision 8 step 4 / H3). The resolver calls
  ``get_serializer_kwargs(info, data=provided_data, instance=<row|None>)`` (the
  finer hook the spec names), then OWNS the merge: ``partial=True`` is injected for
  update (never create) by the FRAMEWORK (a hook returning ``partial`` itself is a
  ``ConfigurationError``); the override's ``context`` dict is merged and
  ``context["request"]`` is set UNCONDITIONALLY to ``request_from_info(info,
  family_label="SerializerMutation")`` (a DIFFERENT ``context["request"]`` object
  is a ``ConfigurationError``, the SAME object tolerated - the request is the
  framework's, the actor the inherited ``check_permission`` seam authorized
  against). The non-overridable ``partial`` / ``context["request"]`` invariants are
  framework-owned and never live in the consumer-overridable hook.

- **Validate via ``serializer.is_valid()``** - a failure maps the nested
  ``serializer.errors`` onto the ``FieldError`` envelope via the dedicated
  **recursive** ``serializer_errors_to_field_errors`` flattener (dotted path
  ``items.0.name``; DRF's ``non_field_errors`` / ``NON_FIELD_ERRORS_KEY`` bucket ->
  the ``"__all__"`` sentinel at every level - NOT the one-level ``036``
  ``validation_error_to_field_errors``), and returns a null-object payload.

- **Write via ``serializer.save()``, wrapped by the ``036`` ``save_or_field_errors``
  ``IntegrityError`` mapper in a value-preserving closure** (the wrapper discards
  its callable's return, so the closure captures ``saved = serializer.save()`` via
  ``nonlocal`` - called EXACTLY ONCE). A save-time ``ValidationError`` routes by
  exception CLASS (F2 / H2): a DRF ``serializers.ValidationError``'s ``.detail`` ->
  the recursive flattener; a Django ``ValidationError`` -> the flat ``036`` mapper
  (``error_dict`` / ``messages``, NEVER ``.detail``); an ``IntegrityError`` ->
  ``save_or_field_errors`` - three separate ``except`` branches (DRF first), never
  a top-level ``GraphQLError``.

- **The re-fetch rides the ``036`` ``refetch_optimized`` G2 path** (Decision 9 /
  G2): the shared skeleton re-fetches the saved object by pk WITHOUT the visibility
  filter, routed through the optimizer so the spec-035 G2 gate keeps
  ``select_related`` / ``prefetch_related`` and applies NO ``.only(...)`` under the
  mutation operation - it comes for free, no new optimizer code.

- **One ``transaction.atomic()`` boundary; the async path runs the sync body in
  one ``sync_to_async(thread_sensitive=True)`` call** - the shared
  ``run_pipeline_async`` boundary both the model and form flavors already delegate
  to, so the three flavors cannot drift on the boundary contract.

DRY-FIRST: the locate / authorize / id-decode / re-fetch / payload / atomic
boundary are the promoted ``036`` skeleton; the flat Django save-time mapper, the
shared ``field_error`` leaf ctor, the ``NON_FIELD_ERROR_KEY`` sentinel, the
``save_or_field_errors`` save mapper, the raw-pk coercion, and the
object-returning ``visible_related_object`` visibility query are all CALLED, not
re-implemented (the spec-039 import manifest). The genuinely net-new code is the
serializer-field-keyed relation decoder and the recursive serializer-error
flattener.
"""

from __future__ import annotations

from typing import Any

import strawberry
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from strawberry import relay

from ..exceptions import ConfigurationError
from ..mutations.inputs import NON_FIELD_ERROR_KEY, FieldError
from ..mutations.resolvers import (
    _coerce_relation_pk_or_none,
    _unencodable_text_error,
    field_error,
    raw_choice_value,
    relation_field_error,
    run_pipeline_async,
    run_write_pipeline_sync,
    save_or_field_errors,
    validation_error_to_field_errors,
)
from ..registry import registry
from ..relay import GlobalIDDecode, decode_model_global_id
from ..utils.permissions import request_from_info
from ..utils.querysets import (
    visibility_scoped_related_queryset,
    visible_related_object,
    visible_related_objects,
)
from .serializer_converter import (
    FILE,
    NESTED_MULTI,
    NESTED_SINGLE,
    RELATION_MULTI,
    RELATION_SINGLE,
    nested_serializer_child,
)

# The async-pipeline recourse appended to a ``SyncMisuseError`` raised when an
# async ``get_queryset`` is met inside the (sync) serializer pipeline. Mirrors the
# ``036`` / ``038`` recourse wording: the whole pipeline runs synchronously (under
# one ``sync_to_async`` worker on the async surface), so an ``async def
# get_queryset`` can never be awaited here.
_SERIALIZER_ASYNC_RECOURSE = (
    "A serializer mutation runs its ORM pipeline synchronously (under one "
    "sync_to_async call on the async surface), so it cannot await an async "
    "get_queryset hook; redefine the target type's get_queryset as a sync method."
)

# DRF's non-field-errors bucket key (``api_settings.NON_FIELD_ERRORS_KEY``,
# default ``"non_field_errors"``). Read once from DRF's settings so the recursive
# flattener normalizes WHATEVER key DRF is configured to use (not a hard-coded
# literal) to the package's ``"__all__"`` sentinel at every level.
_DRF_NON_FIELD_KEY: str = serializers.api_settings.NON_FIELD_ERRORS_KEY


def _relation_field_error(graphql_name: str) -> FieldError:
    """Build the uniform invalid / hidden / wrong-model relation ``FieldError``.

    Keys to the input field's GraphQL wire name (``categoryId``) - what the client
    sent - matching the ``036`` / ``038`` relation-decode contract. Hidden, missing,
    wrong-model, and uncoercible all collapse to this one shape (no existence
    leak). The serializer-path alias for the shared ``relation_field_error`` leaf
    ctor: the message + leaf shape are single-sourced in ``mutations/resolvers.py``
    (spec-039 integration), byte-identical across all three write flavors.
    """
    return relation_field_error(graphql_name)


def _decode_relation_single(
    value: Any,
    *,
    graphql_name: str,
    related_model: type,
    info: Any,
) -> tuple[Any, FieldError | None]:
    """Decode ONE relation id to its visible pk (mirrors the ``038`` form single decoder).

    (i) a ``relay.GlobalID`` runs through ``decode_model_global_id`` against the
    target model (decoded against the target type's RECORDED
    ``effective_globalid_strategy``, never a live settings re-read) - a non-``OK``
    status is a field-keyed ``FieldError``; (ii) a raw pk runs through
    ``_coerce_relation_pk_or_none`` - ``None`` (uncoercible / out of range) is a
    field-keyed ``FieldError``; (iii) for BOTH branches resolve the VISIBLE object
    via the promoted ``visible_related_object`` (P1.1) - a hidden / missing row is
    the SAME field-keyed ``FieldError`` (no existence leak); (iv) reduce the visible
    object to its pk (what DRF's ``PrimaryKeyRelatedField`` expects).

    An explicit ``None`` is NOT an id to decode: it is a clear / no-value passed
    through unchanged so the serializer's own validation decides (a required
    relation raises its field-keyed required error via ``is_valid()``, an optional
    one clears). The generated GraphQL input field exposes only the one
    strategy-dependent shape (Decision 7); this helper accepts BOTH a ``GlobalID``
    and a raw pk because package tests drive the raw-pk / non-Relay branch by direct
    call (M1).
    """
    if value is None:
        return None, None
    pk, error = _type_check_relation_id(
        value,
        graphql_name=graphql_name,
        related_model=related_model,
    )
    if error is not None:
        return None, error
    obj = visible_related_object(related_model, pk, info, _SERIALIZER_ASYNC_RECOURSE)
    if obj is None:
        return None, _relation_field_error(graphql_name)
    return obj.pk, None


def _type_check_relation_id(
    value: Any,
    *,
    graphql_name: str,
    related_model: type,
) -> tuple[Any, FieldError | None]:
    """Type-check + coerce ONE relation id to a pk WITHOUT a DB fetch (spec-039 rev6 #3).

    The STRUCTURAL half of the single decoder, factored out so the batched multi decoder can
    coerce every id first (no per-element fetch), then confirm visibility for the whole set in
    one query: (i) a ``relay.GlobalID`` runs through ``decode_model_global_id`` against the
    target model (a non-``OK`` status is the uniform relation ``FieldError``); (ii) a raw pk
    runs through ``_coerce_relation_pk_or_none`` (``None`` -> the uniform error). Neither
    branch touches the DB - visibility is confirmed by the caller.
    """
    if isinstance(value, relay.GlobalID):
        result = decode_model_global_id(value, related_model)
        if result.status is not GlobalIDDecode.OK:
            return None, _relation_field_error(graphql_name)
        return result.pk, None
    pk = _coerce_relation_pk_or_none(related_model, value)
    if pk is None:
        return None, _relation_field_error(graphql_name)
    return pk, None


def _decode_relation_multi(
    values: Any,
    *,
    graphql_name: str,
    related_model: type,
    info: Any,
) -> tuple[Any, FieldError | None]:
    """Decode an M2M ``list[<id>]`` to visible pks in ONE batched visibility query (spec-039 rev6 #3).

    Type-checks + coerces every element FIRST (no per-element DB fetch, short-circuiting on the
    first structurally-bad id), then confirms the whole set's visibility in ONE ``pk__in`` query
    via the batched ``visible_related_objects`` (instead of one visibility query per element).
    A hidden / missing member collapses to the same field-keyed relation error (no existence
    leak), exactly as the per-element decode did. An explicit ``None`` (the whole list) is
    passed through so the serializer's own required-ness decides; an empty list is a valid clear.
    """
    if values is None:
        return None, None
    pks: list[Any] = []
    for value in values:
        pk, error = _type_check_relation_id(
            value,
            graphql_name=graphql_name,
            related_model=related_model,
        )
        if error is not None:
            return None, error
        pks.append(pk)
    if not pks:
        return [], None
    visible = visible_related_objects(related_model, pks, info, _SERIALIZER_ASYNC_RECOURSE)
    if not {str(pk) for pk in pks} <= visible:
        # A hidden / missing member: the uniform relation error (no existence leak).
        return None, _relation_field_error(graphql_name)
    return pks, None


def _decode_serializer_data(
    mutation_cls: type,
    data: Any,
    info: Any,
) -> tuple[dict[str, Any], FieldError | None]:
    """Decode the bound input dataclass into a serializer-field-keyed ``provided_data`` (NET-NEW).

    The top entry: decodes ``data`` against the bind-stashed top-level reverse map
    (``mutation_cls._input_field_specs``) via the recursive ``_decode_input_object`` (which
    handles nested inputs, rev6 #17). A decode ``FieldError`` short-circuits.
    """
    return _decode_input_object(mutation_cls._input_field_specs, data, info)


def _decode_input_object(
    specs: list,
    data: Any,
    info: Any,
    *,
    path_prefix: str = "",
) -> tuple[dict[str, Any], FieldError | None]:
    """Decode ONE strawberry input dataclass into a serializer-field-keyed dict (spec-039 rev6 #17).

    Walks the provided input fields (``UNSET`` stripped) and, using the per-field reverse map
    (``specs``, keyed by input attr), routes each value by ``kind`` to
    ``result[spec.target_name]`` (the DECLARED serializer field name DRF maps to ``source``
    internally):

    - ``SCALAR`` -> the choice-enum member unwrapped to its raw value via the reused
      ``raw_choice_value`` (with the ``036`` / ``038`` invalid-Unicode preflight).
    - ``RELATION_SINGLE`` / ``RELATION_MULTI`` -> the visibility-checked relation pk(s),
      type-checked against the relation's target model.
    - ``NESTED_SINGLE`` / ``NESTED_MULTI`` -> a RECURSIVELY-decoded nested dict / list of dicts
      (rev6 #17), using the nested reverse map ``spec.nested_specs`` - so a nested relation is
      visibility-checked and a nested scalar Unicode-preflighted exactly like a top-level one.
    - ``FILE`` -> the ``Upload`` value, routed into ``data`` like any other value (the
      deliberate DRF contrast with the form flavor's ``files=`` split).

    ``path_prefix`` is the dotted GraphQL path of the enclosing nested field (empty at the top),
    so a decode ``FieldError`` (a hidden relation id, invalid Unicode) is keyed to its FULL path
    (``shelves.0.altBranches``), not just the leaf name. Re-used recursively for nested items.
    A decode ``FieldError`` short-circuits (the shared skeleton maps it to a null payload).
    """
    spec_by_attr = {spec.input_attr: spec for spec in specs}
    provided_data: dict[str, Any] = {}

    for field in data.__strawberry_definition__.fields:
        python_name = field.python_name
        value = getattr(data, python_name, strawberry.UNSET)
        if value is strawberry.UNSET:
            continue
        spec = spec_by_attr[python_name]
        field_path = _join_path(path_prefix, spec.graphql_name)

        if spec.kind in (RELATION_SINGLE, RELATION_MULTI):
            decoder = (
                _decode_relation_multi if spec.kind == RELATION_MULTI else _decode_relation_single
            )
            decoded, error = decoder(
                value,
                graphql_name=field_path,
                related_model=spec.related_model,
                info=info,
            )
            if error is not None:
                return {}, error
            provided_data[spec.target_name] = decoded
        elif spec.kind in (NESTED_SINGLE, NESTED_MULTI):
            decoded, error = _decode_nested(spec, value, info, path_prefix=field_path)
            if error is not None:
                return {}, error
            provided_data[spec.target_name] = decoded
        elif spec.kind == FILE:
            # An ``Upload`` lands in ``data``, NOT a ``files=`` split: DRF serializers
            # read files from ``data`` (the deliberate contrast with Django forms).
            provided_data[spec.target_name] = value
        else:
            # The same invalid-Unicode preflight the model / form paths apply: a lone
            # surrogate graphql-core accepts as a ``String`` would otherwise reach the
            # serializer's ``validate_unique`` lookup or ``save()`` INSERT and raise a
            # raw ``UnicodeEncodeError`` - a ``ValueError`` neither ``is_valid()`` nor
            # ``save_or_field_errors`` maps - escaping the envelope. Reject it here,
            # keyed to the input's (full-path) GraphQL field name.
            text_error = _unencodable_text_error(field_path, value)
            if text_error is not None:
                return {}, text_error
            provided_data[spec.target_name] = raw_choice_value(value)

    return provided_data, None


def _decode_nested(
    spec: Any,
    value: Any,
    info: Any,
    *,
    path_prefix: str,
) -> tuple[Any, FieldError | None]:
    """Recursively decode a nested input value into nested serializer-keyed data (spec-039 rev6 #17).

    A single nested input dataclass -> one decoded dict (via ``_decode_input_object`` over
    ``spec.nested_specs``); a ``NESTED_MULTI`` list -> a list of decoded dicts, each keyed under
    its index in the path (``shelves.0`` / ``shelves.1``). An explicit ``None`` (a nested clear /
    omitted value that coerced to ``null``) passes through unchanged so the parent serializer's
    OWN validation decides (a required nested field raises its own field-keyed error via
    ``is_valid()``). A decode ``FieldError`` in any nested item short-circuits. The decoded nested
    data is handed to the parent serializer's ``create()`` / ``update()`` (which owns the write -
    the framework never auto-saves the nested relation).
    """
    if value is None:
        return None, None
    if spec.kind == NESTED_MULTI:
        decoded_items: list[dict[str, Any]] = []
        for index, item in enumerate(value):
            item_data, error = _decode_input_object(
                spec.nested_specs,
                item,
                info,
                path_prefix=_join_path(path_prefix, str(index)),
            )
            if error is not None:
                return None, error
            decoded_items.append(item_data)
        return decoded_items, None
    item_data, error = _decode_input_object(
        spec.nested_specs,
        value,
        info,
        path_prefix=path_prefix,
    )
    if error is not None:
        return None, error
    return item_data, None


def serializer_errors_to_field_errors(
    errors: Any,
    reverse_map: dict[str, str],
    *,
    prefix: str = "",
) -> list[FieldError]:
    """Depth-first flatten DRF nested ``serializer.errors`` into the ``FieldError`` envelope (NET-NEW).

    The recursive analog of the flat ``036``
    ``mutations/resolvers.py::validation_error_to_field_errors`` - both terminate in
    the SAME ``field_error`` leaf ctor (spec-039 P2.4), so the ``"__all__"`` sentinel
    + the message coercion cannot drift. DRF's ``serializer.errors`` (and a DRF
    ``ValidationError.detail``) is a nested structure of dicts (per-field), lists
    (indexed children / a field's message list), and leaf strings / ``ErrorDetail``s.
    This walks it depth-first, emitting one ``FieldError`` per leaf:

    - a **dict** recurses each key, joining the dotted path (``items.0.name``);
      DRF's ``non_field_errors`` key (``NON_FIELD_ERRORS_KEY`` =
      ``api_settings.NON_FIELD_ERRORS_KEY``, default ``"non_field_errors"``)
      normalizes to the ``"__all__"`` sentinel segment at THAT level - so a top-level
      bucket becomes the bare ``"__all__"`` and a nested one becomes
      ``<path>.__all__``;
    - a **list of dicts/lists** recurses each child under its index (``items.0``);
    - a **list of leaf messages** (the common ``{field: ["msg", ...]}`` shape) is
      ONE ``FieldError`` for the path with the whole message list;
    - the **ROOT segment** of each emitted leaf path is re-keyed back through the
      reverse map (``serializer field name -> GraphQL input name``) so a relation
      error reports ``categoryId``, not ``category`` (F5), while a nested path keeps
      its child segments verbatim.

    ``reverse_map`` maps each serializer field's declared name (``spec.target_name``)
    to its GraphQL input name (``spec.graphql_name``); a root segment with no entry
    (a nested child key, the ``"__all__"`` sentinel, or a non-reverse-mapped field)
    is kept verbatim.
    """
    if isinstance(errors, dict):
        flattened: list[FieldError] = []
        for key, value in errors.items():
            # The DRF non-field bucket -> the package's ``"__all__"`` sentinel SEGMENT
            # (joined like any other), so a top-level bucket becomes ``"__all__"`` and
            # a nested one ``<path>.__all__``.
            segment = NON_FIELD_ERROR_KEY if str(key) == _DRF_NON_FIELD_KEY else str(key)
            child_prefix = _join_path(prefix, segment)
            flattened.extend(
                serializer_errors_to_field_errors(value, reverse_map, prefix=child_prefix),
            )
        return flattened
    if isinstance(errors, list) and any(isinstance(item, (dict, list)) for item in errors):
        # An indexed list of nested children (``items: [{...}, {...}]``): recurse
        # each under its index. A mixed list never occurs in DRF's error shape, but
        # the guard keeps a stray leaf in such a list from being dropped.
        flattened = []
        for index, item in enumerate(errors):
            child_prefix = _join_path(prefix, str(index))
            flattened.extend(
                serializer_errors_to_field_errors(item, reverse_map, prefix=child_prefix),
            )
        return flattened
    # A leaf: a list of messages, a bare string, or an ``ErrorDetail``. Re-key the
    # ROOT segment through the reverse map, then build the shared leaf - preserving each
    # DRF ``ErrorDetail.code`` alongside the message (rev6 #4) and the structured path
    # (rev6 #13, derived inside ``field_error`` from the dotted key).
    return [
        field_error(
            _rekey_root(prefix, reverse_map),
            errors,
            codes=_error_detail_codes(errors),
        ),
    ]


def _error_detail_codes(errors: Any) -> list[str]:
    """Extract DRF ``ErrorDetail.code``s from a ``serializer.errors`` leaf (spec-039 rev6 #4).

    A DRF leaf is a list of ``ErrorDetail`` (a ``str`` subclass carrying ``.code``), or a
    bare ``ErrorDetail`` / plain string; the codes are read off each element's ``.code`` (a
    plain ``str`` has none -> dropped). Passed to the shared ``field_error`` leaf so the
    serializer envelope carries structured codes a client can branch on (``required`` /
    ``invalid`` / ``unique`` / ``blank`` / ...) without parsing localized human text.
    """
    if isinstance(errors, (list, tuple)):
        return [code for code in (getattr(item, "code", None) for item in errors) if code]
    code = getattr(errors, "code", None)
    return [code] if code else []


def _join_path(prefix: str, segment: str) -> str:
    """Join a dotted-path prefix with a child segment (``items`` + ``0`` -> ``items.0``)."""
    return f"{prefix}.{segment}" if prefix else segment


def _rekey_root(path: str, reverse_map: dict[str, str]) -> str:
    """Re-key a leaf path's ROOT segment through the reverse map; keep child segments verbatim (F5).

    ``category`` -> ``categoryId``; ``items.0.name`` -> ``items.0.name`` (the
    ``items`` root re-keyed if present, the ``0`` / ``name`` children verbatim). An
    empty path (a model-wide ``non_field_errors``) is left empty so ``field_error``
    normalizes it to the ``"__all__"`` sentinel.
    """
    if not path:
        return path
    root, _, rest = path.partition(".")
    mapped = reverse_map.get(root, root)
    return f"{mapped}.{rest}" if rest else mapped


def _reverse_map_for(mutation_cls: type) -> dict[str, str]:
    """Build the ``{serializer field name: GraphQL input name}`` map from the bind-stashed specs."""
    return {spec.target_name: spec.graphql_name for spec in mutation_cls._input_field_specs}


def _merged_serializer_kwargs(
    mutation_cls: type,
    info: Any,
    *,
    provided_data: dict[str, Any],
    instance: Any,
) -> dict[str, Any]:
    """Construct the serializer kwargs through ``get_serializer_kwargs`` + the framework merge (H3).

    Calls the overridable finer hook ``get_serializer_kwargs(info,
    data=provided_data, instance=<row|None>)`` (the spec D8 step-4 hook), then OWNS
    the non-overridable framework rules:

    - ``data`` defaults to ``provided_data`` if the hook omitted it;
    - ``partial=True`` is injected for an UPDATE (``instance is not None``), never
      for create; a hook that set ``partial`` itself is a ``ConfigurationError``
      (the framework owns the partial-update semantics);
    - the override's ``context`` dict is merged, then ``context["request"]`` is set
      UNCONDITIONALLY to the framework request; an override supplying a DIFFERENT
      ``context["request"]`` object is a ``ConfigurationError`` (the request is the
      framework's, the actor the inherited ``check_permission`` authorized against),
      while the SAME object is tolerated.
    """
    kwargs = dict(
        mutation_cls().get_serializer_kwargs(info, data=provided_data, instance=instance),
    )
    kwargs.setdefault("data", provided_data)

    if "partial" in kwargs:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_kwargs returned a "
            "`partial` kwarg; the framework owns partial-update semantics (it injects "
            "partial=True for update, never for create). Remove `partial` from the override.",
        )
    if instance is not None:
        kwargs["partial"] = True

    request = request_from_info(info, family_label="SerializerMutation")
    context = dict(kwargs.get("context") or {})
    override_request = context.get("request")
    if override_request is not None and override_request is not request:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_kwargs set a different "
            "context['request'] object; the framework owns the request context (the actor "
            "check_permission authorized against). Drop context['request'] from the override.",
        )
    context["request"] = request
    kwargs["context"] = context
    return kwargs


def _relation_model_of(field: Any) -> Any:
    """Return the target model a runtime relation field decodes against, or ``None``.

    A single ``PrimaryKeyRelatedField`` carries ``field.queryset.model``; a
    ``ManyRelatedField`` carries it on ``field.child_relation.queryset``. Used by the
    schema/runtime agreement guard to confirm the runtime relation still points at the same
    model the schema-time ``InputFieldSpec.related_model`` recorded.
    """
    related = field.child_relation if isinstance(field, serializers.ManyRelatedField) else field
    return getattr(getattr(related, "queryset", None), "model", None)


def _assert_schema_runtime_agreement(mutation_cls: type, serializer: Any) -> None:
    """Raise ``ConfigurationError`` if the runtime serializer disagrees with the schema field map (rev6 #1).

    The schema-time field map (the ``get_serializer_for_schema()`` hook) drives the generated
    GraphQL input + the bind-stashed reverse map (``mutation_cls._input_field_specs``); the
    runtime write uses the REAL ``serializer_class``. If they diverge, DRF would silently
    ignore an incoming key the GraphQL schema implied is writable (the exact bug the fakeshop
    fixtures once demonstrated). This turns the hook into a VERIFIED contract: for every
    schema-time field spec, the runtime ``serializer.fields`` must

    - contain ``spec.target_name`` and have it WRITABLE (not ``read_only``);
    - bind the SAME ``source`` the schema-time discovery recorded;
    - for a relation, still be a ``PrimaryKeyRelatedField`` (single) / ``ManyRelatedField`` of
      a ``PrimaryKeyRelatedField`` (multi) over the SAME ``related_model``;
    - for a file / scalar, keep a compatible kind (a scalar that moved to a relation or file,
      or vice versa, is a mismatch).

    Runs BEFORE ``is_valid()`` so a schema/runtime mismatch is a framework configuration
    failure (a clear ``ConfigurationError`` at the boundary), never a serializer-validation
    ambiguity. A runtime serializer with EXTRA fields the schema map omits is fine (they are
    simply never provided); only the schema fields are held to the contract.
    """
    for spec in mutation_cls._input_field_specs:
        _assert_field_agreement(mutation_cls, serializer, spec)


def _assert_field_agreement(mutation_cls: type, serializer: Any, spec: Any) -> None:
    """Assert ONE schema-time field spec agrees with the runtime serializer (rev6 #1 / rev2 P1).

    The per-field body of ``_assert_schema_runtime_agreement``, factored out so it serves BOTH
    the input specs (``_input_field_specs``) and the ``Meta.injected_fields`` schema-time specs
    (``_injected_field_specs``): the runtime ``serializer.fields`` must contain
    ``spec.target_name``, have it WRITABLE, bind the SAME ``source``, keep a relation as a
    ``PrimaryKeyRelatedField`` / ``ManyRelatedField(PrimaryKeyRelatedField)`` over the SAME
    ``related_model``, and keep a file / scalar kind compatible. Any divergence is a framework
    ``ConfigurationError`` at the boundary.
    """
    runtime_fields = serializer.fields
    name = type(serializer).__name__
    target = spec.target_name
    runtime = runtime_fields.get(target)
    if runtime is None:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: the schema exposes field "
            f"{target!r}, but the runtime serializer {name} does not declare it. DRF would "
            "silently ignore the incoming value. Make get_serializer_for_schema() and the "
            "runtime serializer_class agree (declare the field on the serializer, or drop it "
            "from the schema field map).",
        )
    if runtime.read_only:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: the schema exposes writable field "
            f"{target!r}, but the runtime serializer {name} declares it read_only; the "
            "incoming value would be ignored. Make the runtime field writable or drop it "
            "from the schema field map.",
        )
    schema_source = spec.source or target
    runtime_source = runtime.source or target
    if runtime_source != schema_source:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: field {target!r} binds source "
            f"{runtime_source!r} at runtime but {schema_source!r} in the schema field map; "
            "the write would target a different attribute than the schema implies. Align "
            "the runtime serializer's source with get_serializer_for_schema().",
        )
    if spec.kind in (RELATION_SINGLE, RELATION_MULTI):
        _assert_relation_agreement(mutation_cls, spec, runtime)
    elif spec.kind in (NESTED_SINGLE, NESTED_MULTI):
        _assert_nested_agreement(mutation_cls, spec, runtime)
    elif spec.kind == FILE:
        if not isinstance(runtime, serializers.FileField):
            raise ConfigurationError(
                f"SerializerMutation {mutation_cls.__name__}: field {target!r} is a file input "
                f"in the schema but {type(runtime).__name__} at runtime; the kind moved. Align "
                "the runtime serializer field with get_serializer_for_schema().",
            )
    elif isinstance(
        runtime,
        (
            serializers.BaseSerializer,
            serializers.RelatedField,
            serializers.ManyRelatedField,
            serializers.FileField,
        ),
    ):
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: field {target!r} is a scalar in the "
            f"schema but a relation / file / nested serializer ({type(runtime).__name__}) at "
            "runtime; the kind moved. Align the runtime serializer field with "
            "get_serializer_for_schema().",
        )


def _assert_relation_agreement(mutation_cls: type, spec: Any, runtime: Any) -> None:
    """Confirm a runtime relation field matches the schema-time relation spec (rev6 #1 helper).

    A ``RELATION_SINGLE`` spec requires a runtime ``PrimaryKeyRelatedField``; a
    ``RELATION_MULTI`` spec requires a ``ManyRelatedField`` wrapping a ``PrimaryKeyRelatedField``
    (the only pk-decoding shapes - spec-039 H5). Either way the runtime relation must point at
    the SAME ``related_model`` the schema-time ``InputFieldSpec`` recorded, so the id decoded
    against the schema target is the id the runtime field validates against.
    """
    if spec.kind == RELATION_SINGLE:
        ok_shape = isinstance(runtime, serializers.PrimaryKeyRelatedField)
    else:
        ok_shape = isinstance(runtime, serializers.ManyRelatedField) and isinstance(
            runtime.child_relation,
            serializers.PrimaryKeyRelatedField,
        )
    if not ok_shape:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: relation field {spec.target_name!r} is "
            f"{type(runtime).__name__} at runtime, but the schema types it as a primary-key "
            "relation; only PrimaryKeyRelatedField (single) / PrimaryKeyRelatedField(many=True) "
            "decode a pk. Align the runtime serializer field with get_serializer_for_schema().",
        )
    runtime_model = _relation_model_of(runtime)
    if runtime_model is not spec.related_model:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: relation field {spec.target_name!r} "
            f"targets {getattr(runtime_model, '__name__', runtime_model)!r} at runtime but "
            f"{getattr(spec.related_model, '__name__', spec.related_model)!r} in the schema field "
            "map; the decoded id would be validated against a different model. Align the runtime "
            "relation's queryset with get_serializer_for_schema().",
        )


def _assert_nested_agreement(mutation_cls: type, spec: Any, runtime: Any) -> None:
    """Confirm a runtime nested serializer field matches the schema-time nested spec (spec-039 rev6 #17).

    A ``NESTED_MULTI`` spec requires a runtime ``ListSerializer`` (a ``many=True`` nested
    serializer); a ``NESTED_SINGLE`` spec requires a plain nested ``Serializer`` (a
    ``BaseSerializer`` that is NOT a ``ListSerializer``). Then the agreement RECURSES: each
    schema-time nested field spec (``spec.nested_specs``) is held to the SAME present / writable /
    source / kind / relation-model / deeper-nested contract against the runtime nested
    serializer's own fields - so a nested shape that drifted between the schema-time hook and the
    runtime serializer is a clear ``ConfigurationError`` at the boundary, at every depth.
    """
    if spec.kind == NESTED_MULTI:
        ok_shape = isinstance(runtime, serializers.ListSerializer)
    else:
        ok_shape = isinstance(runtime, serializers.BaseSerializer) and not isinstance(
            runtime,
            serializers.ListSerializer,
        )
    if not ok_shape:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: nested field {spec.target_name!r} is "
            f"{type(runtime).__name__} at runtime, but the schema types it as a nested "
            f"{'list of serializers' if spec.kind == NESTED_MULTI else 'serializer'}. Align the "
            "runtime serializer field with get_serializer_for_schema().",
        )
    child_serializer, _many = nested_serializer_child(runtime)
    for child_spec in spec.nested_specs:
        _assert_field_agreement(mutation_cls, child_serializer, child_spec)


def _scope_relation_querysets_to_visibility(
    mutation_cls: type,
    serializer: Any,
    info: Any,
) -> None:
    """Intersect each runtime relation field's queryset WITH the visibility queryset (spec-039 rev6 #3).

    For every relation the schema recorded (``_input_field_specs``), narrow the runtime
    serializer field's ``queryset`` (``PrimaryKeyRelatedField``) / ``child_relation.queryset``
    (``ManyRelatedField``) to ``original.filter(pk__in=<visibility queryset>)`` - the author's
    OWN queryset restriction AND-ed with the related primary ``DjangoType``'s visibility-scoped
    ``get_queryset``. Visibility is an ADDITIONAL constraint, never a replacement (rev6 rev2 P1):
    the earlier version REASSIGNED the field queryset, which erased a serializer author's
    intentional ``PrimaryKeyRelatedField(queryset=Branch.objects.filter(city="allowed"))`` and
    could admit a visible-but-serializer-disallowed row. Composing preserves the author's
    contract while still ensuring DRF's own ``is_valid()`` lookup can never re-fetch a row the
    visibility check hid (a single ``pk__in`` subquery - no extra round trip). A relation whose
    target has no registered primary (a raw-pk relation with no visibility contract) is left with
    its own queryset. The agreement guard already ran, so every relation spec has a matching
    writable runtime field over the recorded model (with a non-``None`` queryset).

    **Nested recursion (rev6 #17).** A nested serializer field's OWN relation fields are scoped
    too, by recursing into the runtime nested serializer's ``.fields`` with the nested reverse
    map (``spec.nested_specs``) - so DRF's nested ``is_valid()`` lookup is the visibility lookup
    at every depth, the same defense-in-depth the top level gets.
    """
    _scope_specs_over_serializer(mutation_cls._input_field_specs, serializer, info)


def _scope_specs_over_serializer(specs: list, serializer: Any, info: Any) -> None:
    """Scope one serializer's relation-field querysets to visibility, recursing into nested (rev6 #3 / #17).

    The per-serializer body of ``_scope_relation_querysets_to_visibility``, factored out so it
    serves both the top-level input specs and each nested serializer's specs. A relation field is
    AND-ed with the visibility queryset (never replaced); a nested field recurses into the runtime
    nested serializer's own fields with the nested reverse map.
    """
    for spec in specs:
        if spec.kind in (NESTED_SINGLE, NESTED_MULTI):
            nested_field = serializer.fields.get(spec.target_name)
            if nested_field is None:  # pragma: no cover - the agreement guard already required it.
                continue
            child_serializer, _many = nested_serializer_child(nested_field)
            _scope_specs_over_serializer(spec.nested_specs, child_serializer, info)
            continue
        if spec.kind not in (RELATION_SINGLE, RELATION_MULTI):
            continue
        related_type = registry.get(spec.related_model)
        if related_type is None:
            continue  # raw-pk relation, no visibility contract to scope.
        field = serializer.fields.get(spec.target_name)
        if field is None:  # pragma: no cover - the agreement guard already required it.
            continue
        visible = visibility_scoped_related_queryset(
            related_type,
            info,
            _SERIALIZER_ASYNC_RECOURSE,
        )
        relation = (
            field.child_relation if isinstance(field, serializers.ManyRelatedField) else field
        )
        # Compose (AND), not replace: keep the author's queryset as the base contract and add
        # visibility as a pk__in constraint (a subquery, so still one lookup per field).
        relation.queryset = relation.queryset.filter(pk__in=visible.values("pk"))


def _assert_injected_fields_supplied(mutation_cls: type, serializer: Any) -> None:
    """Verify each ``Meta.injected_fields`` is runtime-ACCEPTED, not merely present (rev6 #2 / rev2 P1).

    ``Meta.injected_fields`` tells the create-required guard that a ``get_serializer_kwargs``
    override supplies those (narrowed-away) required schema-time fields into ``data``. Proving
    the KEY is present is not enough: the RUNTIME serializer must still declare the field,
    writable, with the same source / kind / relation-model the schema-time field had - otherwise
    DRF drops or ignores the injected value and the required field is silently missing. So for
    each injected field this runs the SAME per-field agreement check input fields get (using the
    schema-time ``_injected_field_specs`` stashed at bind), AND confirms the key reached the
    serializer's ``initial_data``. A declared-but-unaccepted / unsupplied injected field is a
    clear ``ConfigurationError``. Only a create with ``injected_fields`` declared is checked.
    """
    injected = mutation_cls._mutation_meta.injected_fields
    if not injected:
        return
    data = getattr(serializer, "initial_data", {}) or {}
    for spec in mutation_cls._injected_field_specs:
        # Same present / writable / source / kind / relation-model checks as an input field:
        # the runtime serializer must actually be able to VALIDATE + SAVE the injected value.
        _assert_field_agreement(mutation_cls, serializer, spec)
        if spec.target_name not in data:
            raise ConfigurationError(
                f"SerializerMutation {mutation_cls.__name__}: Meta.injected_fields declares "
                f"{spec.target_name!r}, but the get_serializer_kwargs override did not supply it "
                "into the serializer data. An injected field must be present in the serializer's "
                "data before validation (supply it from get_serializer_kwargs, or remove it from "
                "Meta.injected_fields).",
            )


def _assert_save_kwargs_no_shadow(mutation_cls: type, save_kwargs: dict[str, Any]) -> None:
    """Raise if a ``get_serializer_save_kwargs`` key shadows a serializer input field (rev6 #12).

    ``serializer.save(**kwargs)`` merges its kwargs OVER the validated data, so a save kwarg
    whose name matches a serializer INPUT field would silently override the client's value. Save
    kwargs are for server-side data NOT in the input (``owner`` / ``created_by``), so a name
    collision with an input field is a configuration mistake - fail loud rather than silently
    clobber. (``_input_field_specs`` is keyed by the declared serializer field name -
    ``spec.target_name`` - the same key DRF's ``validated_data`` uses.)
    """
    input_fields = {spec.target_name for spec in mutation_cls._input_field_specs}
    shadowed = sorted(set(save_kwargs) & input_fields)
    if shadowed:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_save_kwargs returned "
            f"kwarg(s) {shadowed!r} that shadow serializer input field(s); a save kwarg would "
            "silently override the client's input. Save kwargs are for server-side data not in "
            "the input (rename them, or drop the field from the input).",
        )


def _serializer_write_step(
    mutation_cls: type,
    info: Any,
    instance: Any,
    provided_data: dict[str, Any],
) -> Any | list[FieldError]:
    """The serializer ``write_step``: construct -> validate -> save (spec-039 P1.5 callback).

    Constructs the serializer through the ``get_serializer_kwargs`` hook + the
    framework merge (``_merged_serializer_kwargs``), runs ``is_valid()`` (a failure
    routes ``serializer.errors`` through the recursive flattener), then writes via a
    value-preserving ``serializer.save()`` closure wrapped by the ``036``
    ``save_or_field_errors`` (``save()`` called EXACTLY ONCE, captured via
    ``nonlocal``). Returns the saved object (the skeleton re-fetches it by pk under
    the G2 plan) or a ``list[FieldError]`` on a validation / write failure.

    A save-time ``ValidationError`` routes by exception CLASS (F2 / H2) in THREE
    separate ``except`` branches (DRF first): a DRF ``serializers.ValidationError``'s
    ``.detail`` -> the recursive flattener; a Django ``ValidationError`` -> the flat
    ``036`` mapper (``error_dict`` / ``messages``, never ``.detail``); an
    ``IntegrityError`` -> ``save_or_field_errors`` - never a top-level
    ``GraphQLError`` at the write.
    """
    serializer_class = mutation_cls._mutation_meta.serializer_class
    reverse_map = _reverse_map_for(mutation_cls)
    kwargs = _merged_serializer_kwargs(
        mutation_cls,
        info,
        provided_data=provided_data,
        instance=instance,
    )
    serializer = serializer_class(**kwargs)

    # rev6 #1: PROVE the schema-time field map and the runtime serializer AGREE before
    # ``is_valid()`` runs, so a schema hook that exposed a field the runtime serializer does
    # not actually declare (or declares with a different source / relation target / kind) is a
    # framework CONFIGURATION failure - a clear ``ConfigurationError`` - not a silent
    # DRF-ignores-the-unknown-key ambiguity. The schema hook becomes a verified contract.
    _assert_schema_runtime_agreement(mutation_cls, serializer)
    # rev6 #2: verify the ``Meta.injected_fields`` the create-required guard trusted the
    # get_serializer_kwargs override to supply ACTUALLY reached the serializer's data, so a
    # declared-but-unsupplied injected field is a clear ConfigurationError, not a silent
    # validation failure.
    _assert_injected_fields_supplied(mutation_cls, serializer)
    # rev6 #3: adapt each relation field's queryset to the SAME visibility-scoped queryset the
    # decode used, so DRF's own ``is_valid()`` lookup is the VISIBILITY lookup rather than an
    # unscoped second fetch (defense in depth - DRF can never re-fetch a row the decode's
    # visibility check hid, even if the decode is bypassed).
    _scope_relation_querysets_to_visibility(mutation_cls, serializer, info)

    if not serializer.is_valid():
        return serializer_errors_to_field_errors(serializer.errors, reverse_map)

    # rev6 #12: the DRF-native ``serializer.save(**kwargs)`` customization point (request-derived
    # save-time data, e.g. ``owner=request.user``), distinct from the constructor
    # ``get_serializer_kwargs``. Rejected if a save kwarg would shadow a serializer input field
    # (it would silently override the client's value). Called INSIDE the value-preserving
    # closure, so the transaction / error-mapping / optimizer re-fetch behavior is preserved.
    save_kwargs = dict(mutation_cls().get_serializer_save_kwargs(info, provided_data, instance))
    _assert_save_kwargs_no_shadow(mutation_cls, save_kwargs)

    saved: Any = None

    def _do_save() -> None:
        nonlocal saved
        saved = serializer.save(**save_kwargs)

    try:
        write_error = save_or_field_errors(_do_save)
    except DRFValidationError as exc:
        return serializer_errors_to_field_errors(exc.detail, reverse_map)
    except DjangoValidationError as exc:
        return validation_error_to_field_errors(exc)
    if write_error is not None:
        return write_error
    return saved


def resolve_serializer_sync(
    mutation_cls: type,
    info: Any,
    *,
    data: Any = strawberry.UNSET,
    id: Any = strawberry.UNSET,  # noqa: A002
) -> Any:
    """Sync serializer-pipeline entry the base's ``resolve_sync`` delegates to (spec-039 Decision 8).

    The serializer-flavor parallel of ``resolve_mutation_sync`` /
    ``resolve_form_sync``: a thin public entry that delegates to the promoted shared
    ``run_write_pipeline_sync`` skeleton (the ``transaction.atomic()`` boundary +
    locate preamble + authorize-before-decode ordering + optimizer re-fetch tail are
    single-sited there), supplying only the serializer ``decode_step`` (the
    serializer-field-keyed relation/scalar/file decode) and ``write_step``
    (construct / ``is_valid`` / ``save``) callbacks.
    """
    return run_write_pipeline_sync(
        mutation_cls,
        info,
        data,
        id,
        decode_step=lambda _instance: _serializer_decode_step(mutation_cls, data, info),
        write_step=lambda instance, decoded: _serializer_write_step(
            mutation_cls,
            info,
            instance,
            decoded,
        ),
    )


def _serializer_decode_step(
    mutation_cls: type,
    data: Any,
    info: Any,
) -> dict[str, Any] | list[FieldError]:
    """The serializer ``decode_step``: serializer-field-keyed decode (spec-039 P1.5 callback).

    Decodes the bound input into a serializer-field-keyed ``provided_data`` (the
    ``_decode_serializer_data`` contract: type-check + visibility on every relation
    branch, ``Upload`` into ``data``). Returns ``provided_data`` for the write step,
    or a ``list[FieldError]`` on a decode failure (the shared skeleton maps it to a
    null-object payload). The ``instance`` the skeleton locates is not needed at
    decode (DRF's ``partial=True`` + the framework merge own the partial update at
    construction), so it is not threaded in.
    """
    provided_data, decode_error = _decode_serializer_data(mutation_cls, data, info)
    if decode_error is not None:
        return [decode_error]
    return provided_data


async def resolve_serializer_async(
    mutation_cls: type,
    info: Any,
    *,
    data: Any = strawberry.UNSET,
    id: Any = strawberry.UNSET,  # noqa: A002
) -> Any:
    """Async serializer-pipeline entry: the sync body in one ``sync_to_async(thread_sensitive=True)``.

    Delegates to the shared ``mutations/resolvers.py::run_pipeline_async`` boundary
    (single-sourced with the model + form flavors - the same ``036`` boundary shape)
    so the ``transaction.atomic()`` + every ORM call run on one worker thread, never
    interleaving ORM work with ``await``s. A sync ``get_queryset`` runs synchronously
    inside that thread; an ``async def get_queryset`` raises ``SyncMisuseError``
    there.
    """
    return await run_pipeline_async(_run_serializer_pipeline_sync, mutation_cls, info, data, id)


def _run_serializer_pipeline_sync(
    mutation_cls: type,
    info: Any,
    data: Any,
    id: Any,  # noqa: A002
) -> Any:
    """The positional-arg sync body the shared ``run_pipeline_async`` boundary wraps.

    ``run_pipeline_async`` calls ``sync_body(mutation_cls, info, data, id)``
    positionally; ``resolve_serializer_sync`` takes ``data`` / ``id`` as
    ``UNSET``-default kwargs, so this thin adapter normalizes the positional call to
    it (the ``036`` ``_run_pipeline_sync`` / ``resolve_mutation_sync`` relationship).
    """
    return resolve_serializer_sync(mutation_cls, info, data=data, id=id)
