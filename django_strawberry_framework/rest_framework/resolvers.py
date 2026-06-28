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
  pk - is type-checked against the relation's **target model** (resolved from the
  backing FK via the serializer field's ``source``, or ``field.queryset.model``
  for a serializer-only relation), then **resolved to the visible object through
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
from ..relay import GlobalIDDecode, decode_model_global_id
from ..utils.permissions import request_from_info
from ..utils.querysets import visible_related_object
from .inputs import get_serializer_for_schema
from .serializer_converter import FILE, RELATION_MULTI, RELATION_SINGLE

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


def _relation_target_models(mutation_cls: type) -> dict[str, type]:
    """Map each relation serializer-field name to its Django target model (Decision 7).

    Re-reads the serializer's SCHEMA-TIME field set (the same
    ``get_serializer_for_schema`` discovery the Slice-1 converter used at build) and,
    for each relation field, resolves the target model the way the converter
    recorded it: a ``PrimaryKeyRelatedField`` exposes ``field.queryset.model``; a
    ``ManyRelatedField`` exposes ``field.child_relation.queryset.model``. This is the
    SAME basis the converter's ``serializer_only_relation_annotation`` /
    ``backing_model_field`` resolution used, so the decode type-checks each id
    against the model the build site typed the input over. Keyed by the declared
    serializer field name (``spec.target_name``).
    """
    fields = get_serializer_for_schema(mutation_cls._mutation_meta.serializer_class)
    target_models: dict[str, type] = {}
    for name, field in fields.items():
        related_field = (
            field.child_relation if isinstance(field, serializers.ManyRelatedField) else field
        )
        queryset = getattr(related_field, "queryset", None)
        model = getattr(queryset, "model", None)
        if model is not None:
            target_models[name] = model
    return target_models


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
    if isinstance(value, relay.GlobalID):
        result = decode_model_global_id(value, related_model)
        if result.status is not GlobalIDDecode.OK:
            return None, _relation_field_error(graphql_name)
        pk = result.pk
    else:
        pk = _coerce_relation_pk_or_none(related_model, value)
        if pk is None:
            return None, _relation_field_error(graphql_name)

    obj = visible_related_object(related_model, pk, info, _SERIALIZER_ASYNC_RECOURSE)
    if obj is None:
        return None, _relation_field_error(graphql_name)
    return obj.pk, None


def _decode_relation_multi(
    values: Any,
    *,
    graphql_name: str,
    related_model: type,
    info: Any,
) -> tuple[Any, FieldError | None]:
    """Decode an M2M ``list[<id>]`` to a list of visible pks (mirrors the ``038`` form multi decoder).

    Maps ``_decode_relation_single`` over each element (every member type-checked,
    visibility-checked on its own branch, reduced to its pk); the first member error
    short-circuits. An explicit ``None`` (the whole list) is passed through so the
    serializer's own required-ness decides; an empty list is a valid clear.
    """
    if values is None:
        return None, None
    pks: list[Any] = []
    for value in values:
        pk, error = _decode_relation_single(
            value,
            graphql_name=graphql_name,
            related_model=related_model,
            info=info,
        )
        if error is not None:
            return None, error
        pks.append(pk)
    return pks, None


def _decode_serializer_data(
    mutation_cls: type,
    data: Any,
    info: Any,
) -> tuple[dict[str, Any], FieldError | None]:
    """Decode the bound input dataclass into a serializer-field-keyed ``provided_data`` (NET-NEW).

    Walks the provided input fields (``UNSET`` stripped) and, using the bind-stashed
    per-field reverse map (``mutation_cls._input_field_specs``, keyed by input attr),
    routes each value by ``kind`` to ``provided_data[spec.target_name]`` (the
    DECLARED serializer field name DRF maps to ``source`` internally):

    - ``SCALAR`` -> the choice-enum member unwrapped to its raw value via the reused
      ``raw_choice_value`` (with the ``036`` / ``038`` invalid-Unicode preflight).
    - ``RELATION_SINGLE`` / ``RELATION_MULTI`` -> the visibility-checked relation
      pk(s), type-checked against the relation's target model.
    - ``FILE`` -> the ``Upload`` value, routed into ``data`` like any other value
      (the deliberate DRF contrast with the form flavor's ``files=`` split).

    A relation decode ``FieldError`` short-circuits.
    """
    spec_by_attr = {spec.input_attr: spec for spec in mutation_cls._input_field_specs}
    target_models = _relation_target_models(mutation_cls)
    provided_data: dict[str, Any] = {}

    for field in data.__strawberry_definition__.fields:
        python_name = field.python_name
        value = getattr(data, python_name, strawberry.UNSET)
        if value is strawberry.UNSET:
            continue
        spec = spec_by_attr[python_name]

        if spec.kind in (RELATION_SINGLE, RELATION_MULTI):
            decoder = (
                _decode_relation_multi if spec.kind == RELATION_MULTI else _decode_relation_single
            )
            decoded, error = decoder(
                value,
                graphql_name=spec.graphql_name,
                related_model=target_models[spec.target_name],
                info=info,
            )
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
            # keyed to the input's GraphQL field name.
            text_error = _unencodable_text_error(spec.graphql_name, value)
            if text_error is not None:
                return {}, text_error
            provided_data[spec.target_name] = raw_choice_value(value)

    return provided_data, None


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
    # ROOT segment through the reverse map, then build the shared leaf.
    return [field_error(_rekey_root(prefix, reverse_map), errors)]


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
    from ..exceptions import ConfigurationError

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

    if not serializer.is_valid():
        return serializer_errors_to_field_errors(serializer.errors, reverse_map)

    saved: Any = None

    def _do_save() -> None:
        nonlocal saved
        saved = serializer.save()

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
