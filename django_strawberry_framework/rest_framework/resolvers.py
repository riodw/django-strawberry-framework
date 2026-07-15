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

- **The serializer is constructed via the CONSTRUCTOR-ONLY ``get_serializer_kwargs``
  hook + the framework merge** (Decision 8 step 4 / H3, hardened). The framework
  builds the authoritative serializer ``data`` ITSELF - decoded client data plus the
  ``get_serializer_injected_data`` injection (whose keys must EXACTLY match
  ``Meta.injected_fields``) - then calls ``get_serializer_kwargs(info, data=<copy>,
  instance=<row|None>)`` for constructor kwargs only. ``data``, ``instance``,
  ``partial``, ``context["request"]``, and ``context["write_alias"]`` are
  FRAMEWORK-OWNED: a conflicting reserved return (a differing ``data``, a
  substituted ``instance``, any ``partial``, a different ``context["request"]``
  object, a conflicting ``context["write_alias"]``) is a ``ConfigurationError``;
  equal / identical returns are tolerated. ``partial=True`` is injected for update
  (never create); ``context["request"]`` is the framework request (the actor the
  inherited ``check_permission`` seam authorized against);
  ``context["write_alias"]`` is the pipeline's pinned write alias so custom
  serializer code stays inside the one transaction.

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

import copy
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

import strawberry
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.signals import post_save, pre_save
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from ..exceptions import ConfigurationError
from ..mutations.inputs import NON_FIELD_ERROR_KEY, FieldError
from ..mutations.resolvers import (
    make_resolver_entries,
    run_write_pipeline_sync,
    save_or_field_errors,
)
from ..utils.errors import (
    field_error,
    join_error_path,
    relation_field_error,
    validation_error_to_field_errors,
)
from ..utils.permissions import request_from_info
from ..utils.querysets import (
    pks_all_present,
    related_visibility_queryset,
    sync_pipeline_recourse,
    visible_related_objects,
)
from ..utils.write_transaction import (
    base_locked_queryset,
    pin_write_queryset,
    require_write_pipeline,
)
from ..utils.write_values import (
    decode_provided_fields,
    decode_scalar_leaf,
    decode_visible_relation,
    type_check_relation_id,
)
from .inputs import runtime_validated_data_fields, writable_source_collisions
from .serializer_converter import (
    FILE,
    NESTED_MULTI,
    NESTED_SINGLE,
    RELATION_MULTI,
    RELATION_SINGLE,
    nested_serializer_child,
)

# The omission sentinel the reserved serializer-kwarg checks use: it keeps an
# explicit ``data=None`` / ``instance=None`` return distinguishable from a hook
# that simply omitted the key (a ``pop(..., None)`` default would conflate the
# two, silently forgiving an explicit ``None``).
_OMITTED = object()

# The async-pipeline recourse appended to a ``SyncMisuseError`` raised when an
# async ``get_queryset`` is met inside the (sync) serializer pipeline. Mirrors the
# ``036`` / ``038`` recourse wording: the whole pipeline runs synchronously (under
# one ``sync_to_async`` worker on the async surface), so an ``async def
# get_queryset`` can never be awaited here. Single-sourced across the three write
# flavors via ``sync_pipeline_recourse`` (spec-039 Md2).
_SERIALIZER_ASYNC_RECOURSE = sync_pipeline_recourse("serializer mutation")

# DRF's non-field-errors bucket key (``api_settings.NON_FIELD_ERRORS_KEY``,
# default ``"non_field_errors"``). Read once from DRF's settings so the recursive
# flattener normalizes WHATEVER key DRF is configured to use (not a hard-coded
# literal) to the package's ``"__all__"`` sentinel at every level.
_DRF_NON_FIELD_KEY: str = serializers.api_settings.NON_FIELD_ERRORS_KEY


def _decode_relation_single(
    value: Any,
    *,
    graphql_name: str,
    related_model: type,
    info: Any,
) -> tuple[Any, FieldError | None]:
    """Decode ONE relation id to its visible pk (mirrors the ``038`` form single decoder).

    The serializer coloring of the shared
    ``utils/write_values.py::decode_visible_relation`` spine (DRY review A1):
    type-check + pk coercion -> visible object (a hidden / missing / wrong-model
    / uncoercible id is the uniform field-keyed ``FieldError``, no existence
    leak) -> the pk projection (what DRF's ``PrimaryKeyRelatedField`` expects).

    An explicit ``None`` is NOT an id to decode: it is a clear / no-value skipped
    through unchanged so the serializer's own validation decides (a required
    relation raises its field-keyed required error via ``is_valid()``, an optional
    one clears). The generated GraphQL input field exposes only the one
    strategy-dependent shape (Decision 7); this helper accepts BOTH a ``GlobalID``
    and a raw pk because package tests drive the raw-pk / non-Relay branch by direct
    call (M1).
    """
    return decode_visible_relation(
        value,
        graphql_name=graphql_name,
        related_model=related_model,
        info=info,
        async_recourse=_SERIALIZER_ASYNC_RECOURSE,
        skip=lambda candidate: candidate is None,
        project=lambda obj: obj.pk,
    )


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
        pk, error = type_check_relation_id(
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
    if not pks_all_present(pks, visible):
        # A hidden / missing member: the uniform relation error (no existence leak).
        return None, relation_field_error(graphql_name)
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

    - ``SCALAR`` -> through the shared scalar leaf ``decode_scalar_leaf`` (the ``036`` /
      ``038`` invalid-Unicode preflight + choice-enum unwrap).
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

    The reverse-map build + the ``UNSET``-strip walk + the kind dispatch are single-sited in
    ``utils/write_values.py::decode_provided_fields`` (DRY review A2); the handlers below carry
    the SERIALIZER destination policy (everything into ``data``, incl. the ``NESTED_*``
    recursion and the full-path error keying).
    """
    provided_data: dict[str, Any] = {}

    def _field_path(spec: Any) -> str:
        return join_error_path(path_prefix, spec.graphql_name)

    def _relation(spec: Any, value: Any) -> FieldError | None:
        decoder = (
            _decode_relation_multi if spec.kind == RELATION_MULTI else _decode_relation_single
        )
        decoded, error = decoder(
            value,
            graphql_name=_field_path(spec),
            related_model=spec.related_model,
            info=info,
        )
        if error is not None:
            return error
        provided_data[spec.target_name] = decoded
        return None

    def _nested(spec: Any, value: Any) -> FieldError | None:
        decoded, error = _decode_nested(spec, value, info, path_prefix=_field_path(spec))
        if error is not None:
            return error
        provided_data[spec.target_name] = decoded
        return None

    def _file(spec: Any, value: Any) -> None:
        # An ``Upload`` lands in ``data``, NOT a ``files=`` split: DRF serializers
        # read files from ``data`` (the deliberate contrast with Django forms).
        provided_data[spec.target_name] = value
        return None

    def _scalar(spec: Any, value: Any) -> FieldError | None:
        # The shared scalar leaf (invalid-Unicode preflight + choice-enum unwrap,
        # ``decode_scalar_leaf``), keyed to the input's (full-path) GraphQL field
        # name so a lone surrogate never escapes the envelope as a raw
        # ``UnicodeEncodeError`` at the serializer's ``save()`` / unique lookup.
        decoded, text_error = decode_scalar_leaf(_field_path(spec), value)
        if text_error is not None:
            return text_error
        provided_data[spec.target_name] = decoded
        return None

    error = decode_provided_fields(
        specs,
        data,
        handlers={
            RELATION_SINGLE: _relation,
            RELATION_MULTI: _relation,
            NESTED_SINGLE: _nested,
            NESTED_MULTI: _nested,
            FILE: _file,
        },
        scalar_handler=_scalar,
    )
    if error is not None:
        return {}, error
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
                path_prefix=join_error_path(path_prefix, str(index)),
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
    reverse_map: dict[str, tuple[str, dict | None]],
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

    - a **dict** recurses each key, joining the dotted path (``items.0.name``); each key is
      RE-KEYED to its GraphQL name AS IT DESCENDS (not only the root - rev6 #17 review P2),
      using the RECURSIVE ``reverse_map``, so a nested child field / alias / relation suffix
      reports its GraphQL name (``shelves.0.altBranches``, not ``shelves.0.alt_branches``).
      DRF's ``non_field_errors`` key (``NON_FIELD_ERRORS_KEY`` = ``api_settings.NON_FIELD_ERRORS_KEY``,
      default ``"non_field_errors"``) normalizes to the ``"__all__"`` sentinel segment at THAT
      level - so a top-level bucket becomes the bare ``"__all__"`` and a nested one
      ``<path>.__all__``;
    - a **list of dicts/lists** recurses each child under its NUMERIC index (``items.0``),
      carrying the SAME level reverse map (the list items are the same nested serializer);
    - a **list of leaf messages** (the common ``{field: ["msg", ...]}`` shape) is ONE
      ``FieldError`` for the (already-re-keyed) path with the whole message list.

    ``reverse_map`` is the RECURSIVE reverse map from ``_build_reverse_map`` -
    ``{serializer field name: (GraphQL input name, child_map | None)}`` - so each nesting level
    re-keys with its OWN field map. A segment with no entry (a numeric index, the ``"__all__"``
    sentinel, or a non-mapped field) is kept verbatim.
    """
    if isinstance(errors, dict):
        flattened: list[FieldError] = []
        for key, value in errors.items():
            # Re-key THIS dict key to its GraphQL name and descend with the child level's map,
            # so every segment (not just the root) reports the GraphQL name (rev6 #17 review P2).
            segment, child_map = _rekey_segment(str(key), reverse_map)
            child_prefix = join_error_path(prefix, segment)
            flattened.extend(
                serializer_errors_to_field_errors(value, child_map, prefix=child_prefix),
            )
        return flattened
    if isinstance(errors, list) and any(isinstance(item, (dict, list)) for item in errors):
        # An indexed list of nested children (``items: [{...}, {...}]``): recurse each under its
        # index, keeping the SAME reverse map (each item is the same nested serializer). A mixed
        # list never occurs in DRF's error shape, but the guard keeps a stray leaf from dropping.
        flattened = []
        for index, item in enumerate(errors):
            child_prefix = join_error_path(prefix, str(index))
            flattened.extend(
                serializer_errors_to_field_errors(item, reverse_map, prefix=child_prefix),
            )
        return flattened
    # A leaf: a list of messages, a bare string, or an ``ErrorDetail``. The ``prefix`` is already
    # fully re-keyed during descent, so build the shared leaf directly - preserving each DRF
    # ``ErrorDetail.code`` alongside the message (rev6 #4) and the structured path (rev6 #13,
    # derived inside ``field_error`` from the dotted key).
    return [
        field_error(
            prefix,
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


def _rekey_segment(
    key: str,
    reverse_map: dict[str, tuple[str, dict | None]],
) -> tuple[str, dict[str, tuple[str, dict | None]]]:
    """Re-key ONE dict segment to its GraphQL name + return the CHILD level's reverse map (review P2).

    The DRF non-field bucket normalizes to the ``"__all__"`` sentinel (with no child map); a
    reverse-mapped serializer field returns its GraphQL name + its nested child map (``{}`` when
    the field is not itself nested); an unmapped key (a numeric index reached as a dict key, or a
    non-input field) is kept verbatim with no child map. So each nesting level re-keys with its
    OWN field map, not only the root.
    """
    if key == _DRF_NON_FIELD_KEY:
        return NON_FIELD_ERROR_KEY, {}
    mapped = reverse_map.get(key) if reverse_map else None
    if mapped is None:
        return key, {}
    graphql_name, child_map = mapped
    return graphql_name, (child_map or {})


def _build_reverse_map(specs: list) -> dict[str, tuple[str, dict | None]]:
    """Build the RECURSIVE reverse map from the bind-stashed input specs (rev6 #17 review P2).

    ``{serializer field name (spec.target_name): (GraphQL input name (spec.graphql_name),
    child_map | None)}`` - a nested field's ``child_map`` is the recursive reverse map of its
    ``nested_specs``, so ``serializer_errors_to_field_errors`` re-keys nested child fields /
    aliases / relation suffixes to their GraphQL names at every depth (not just the root). A
    non-nested field has ``child_map=None``.
    """
    result: dict[str, tuple[str, dict | None]] = {}
    for spec in specs:
        child = _build_reverse_map(spec.nested_specs) if spec.nested_specs is not None else None
        result[spec.target_name] = (spec.graphql_name, child)
    return result


def _plain_container_clone(value: Any) -> Any:
    """Recursively clone the plain ``dict`` / ``list`` containers of a decoded data tree.

    The hardened hooks (``get_serializer_injected_data`` / ``get_serializer_kwargs``)
    receive a COPY of the framework-built serializer data so mutating it has no
    effect on the authoritative structure. A shallow ``dict(...)`` copy only
    detaches the OUTER mapping - a hook could still mutate a nested list / dict in
    place. This clones every plain container recursively while passing opaque
    leaves (scalars, model instances, uploaded files) through by reference, so the
    copy is structurally independent without duplicating unclonable objects.

    Iterative (an explicit stack), NOT recursive: a ``JSONField`` input is
    client-controlled and json-parseable nesting easily exceeds Python's recursion
    limit, so a recursive clone would let a deeply-nested payload crash the
    pipeline with a ``RecursionError`` (an availability hole, not a validation
    error).
    """
    if not isinstance(value, (dict, list)):
        return value

    def _fresh(container: Any) -> Any:
        return {} if isinstance(container, dict) else []

    def _entries(container: Any) -> Any:
        return (
            iter(container.items()) if isinstance(container, dict) else iter(enumerate(container))
        )

    def _place(target: Any, key: Any, child: Any) -> None:
        if isinstance(target, dict):
            target[key] = child
        else:
            target.append(child)

    # ``memo`` maps each seen source container to its clone, so a SHARED (diamond)
    # reference clones once and stays shared in the copy; ``active`` tracks the ancestor
    # path, so a genuine CYCLE (a container transitively containing itself - impossible
    # in parsed GraphQL JSON, but constructible by a hook) fails loud instead of looping
    # forever. The sources stay alive via the caller's tree, so id() keys cannot be reused.
    root: Any = _fresh(value)
    memo: dict[int, Any] = {id(value): root}
    active: set[int] = {id(value)}
    stack: list[tuple[Any, Any, Any]] = [(value, root, _entries(value))]
    while stack:
        source, target, entries = stack[-1]
        descended = False
        for key, item in entries:
            if not isinstance(item, (dict, list)):
                _place(target, key, item)
                continue
            item_id = id(item)
            if item_id in active:
                raise ConfigurationError(
                    "SerializerMutation hook data contains a CYCLIC container (a dict or "
                    "list that transitively contains itself); cyclic data cannot be cloned "
                    "or validated. Break the cycle in the hook-supplied structure.",
                )
            child = memo.get(item_id)
            if child is None:
                child = _fresh(item)
                memo[item_id] = child
                _place(target, key, child)
                active.add(item_id)
                stack.append((item, child, _entries(item)))
                descended = True
                break
            _place(target, key, child)
        if not descended:
            active.discard(id(source))
            stack.pop()
    return root


def _injected_serializer_data(
    mutation_cls: type,
    info: Any,
    *,
    provided_data: dict[str, Any],
    instance: Any,
) -> dict[str, Any]:
    """Collect the ``Meta.injected_fields`` values through ``get_serializer_injected_data``.

    The declared-injection half of the final serializer data (the hardening pass):
    the framework builds the authoritative data itself from the DECODED client data
    plus this hook's return - a ``get_serializer_kwargs`` override can no longer
    replace or extend ``data``. The hook receives a recursive plain-container CLONE
    of the decoded client data (mutating it - even a nested list or dict - has no
    effect), and its returned keys must EXACTLY match
    ``Meta.injected_fields``: a missing declared field would silently fail
    validation, an undeclared extra key would smuggle a value past the auditable
    contract - both are a loud ``ConfigurationError``. Class validation already
    guarantees an injected field is never also a GraphQL input field, so the merge
    can never overwrite a client value.
    """
    declared = frozenset(mutation_cls._mutation_meta.injected_fields or ())
    injected = dict(
        mutation_cls().get_serializer_injected_data(
            info,
            data=_plain_container_clone(provided_data),
            instance=instance,
        ),
    )
    if set(injected) != declared:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_injected_data returned "
            f"key(s) {sorted(injected)!r}, but Meta.injected_fields declares "
            f"{sorted(declared)!r}. The hook must supply EXACTLY the declared injected fields - "
            "declare every supplied field in Meta.injected_fields and supply every declared one.",
        )
    return injected


def _merged_serializer_kwargs(
    mutation_cls: type,
    info: Any,
    *,
    final_data: dict[str, Any],
    instance: Any,
    alias: str,
) -> dict[str, Any]:
    """Construct the serializer kwargs through ``get_serializer_kwargs`` + the framework merge (H3).

    Calls the overridable CONSTRUCTOR-ONLY hook ``get_serializer_kwargs(info,
    data=<copy>, instance=<row|None>)`` (the spec D8 step-4 hook), then OWNS the
    non-overridable framework rules. ``data``, ``instance``, ``partial``,
    ``context["request"]``, and ``context["write_alias"]`` are FRAMEWORK-OWNED:

    - ``data`` is the framework-built final data (decoded client data + declared
      injection); the hook receives a recursive plain-container CLONE (nested
      mutations have no effect either), and the returned ``data`` must be either
      OMITTED or the exact clone object the hook received (identity, checked via
      an omission sentinel) - anything else, including an explicit ``None``, is a
      ``ConfigurationError`` (the old replace-the-decoded-data bypass). Identity
      rather than equality: a deep comparison of two independently cloned
      structures would recurse (deep valid payloads crash it), and equality
      cannot see a semantically different reordering of exotic mappings.
    - ``instance`` is the located, authorized row; a returned ``instance`` that is
      not THAT object (omission-sentinel + identity again, so an explicit
      ``instance=None`` on update is rejected too) is a ``ConfigurationError``
      (the old substitute-the-target bypass - row A's authorization must never
      write row B).
    - ``partial`` is injected for an UPDATE (``instance is not None``), never for
      create; a hook that set ``partial`` itself is a ``ConfigurationError``.
    - the override's ``context`` dict is merged, then ``context["request"]`` is set
      UNCONDITIONALLY to the framework request (a DIFFERENT object is a
      ``ConfigurationError``, the SAME object tolerated) and
      ``context["write_alias"]`` to the pipeline's pinned write alias (a
      conflicting value is a ``ConfigurationError``) - so a custom serializer hook
      that queries or defers work can read the ONE alias the transaction covers.
    """
    data_clone = _plain_container_clone(final_data)
    kwargs = dict(
        mutation_cls().get_serializer_kwargs(
            info,
            data=data_clone,
            instance=instance,
        ),
    )

    # The reserved-key checks use an omission SENTINEL + object IDENTITY, never
    # equality: a deep ``!=`` over two independently cloned structures recurses
    # (a ~1,500-level valid payload would crash the comparison even though the
    # clone itself is iterative), and a ``pop(..., None)`` default would make an
    # explicit ``data=None`` / ``instance=None`` indistinguishable from
    # omission. A hook may omit the key or pass back the EXACT object it
    # received (the default's pass-through); anything else fails closed.
    returned_data = kwargs.pop("data", _OMITTED)
    if returned_data is not _OMITTED and returned_data is not data_clone:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_kwargs returned a "
            "`data` value that is not the exact object the hook received; `data` is "
            "framework-owned (decoded client input plus Meta.injected_fields injection), so "
            "the hook must pass it through unchanged or omit it. Supply extra fields via "
            "get_serializer_injected_data + Meta.injected_fields, not by rewriting `data`.",
        )
    kwargs["data"] = final_data

    returned_instance = kwargs.pop("instance", _OMITTED)
    if returned_instance is not _OMITTED and returned_instance is not instance:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_kwargs returned a "
            "different `instance` than the located, authorized row; `instance` is "
            "framework-owned (authorization is point-in-time against the located row, so a "
            "substituted instance would write a row the caller was never authorized for).",
        )

    if "partial" in kwargs:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_kwargs returned a "
            "`partial` kwarg; the framework owns partial-update semantics (it injects "
            "partial=True for update, never for create). Remove `partial` from the override.",
        )
    if instance is not None:
        kwargs["instance"] = instance
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
    override_alias = context.get("write_alias")
    if override_alias is not None and override_alias != alias:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_kwargs set "
            f"context['write_alias'] to {override_alias!r}, but the mutation's transaction is "
            f"pinned to {alias!r}; the write alias is framework-owned (one transaction, one "
            "alias). Drop context['write_alias'] from the override.",
        )
    context["request"] = request
    context["write_alias"] = alias
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


def _assert_runtime_write_source_ownership(
    mutation_cls: type,
    serializer: Any,
    data: Mapping[str, Any],
    specs: list,
    *,
    path: str = "",
) -> None:
    """Reject runtime fields that can overwrite one another in ``validated_data``.

    Schema discovery cannot see context-dependent fields returned by ``get_fields()``. Walk the
    instantiated serializer immediately before validation, including every explicitly opted-in
    nested serializer, so hidden/defaulted runtime fields cannot silently replace client or
    injected values through DRF's last-write-wins source assignment.
    """
    supplied_fields = set(data)
    runtime_fields = runtime_validated_data_fields(
        serializer.fields,
        supplied_fields=supplied_fields,
        apply_defaults=mutation_cls._mutation_meta.operation == "create",
    )
    colliding = writable_source_collisions(
        {field_name: field.source for field_name, field in runtime_fields.items()},
    )
    if colliding:
        location = path or "<root>"
        detail = "; ".join(
            f"source {source!r} <- fields {owners!r}"
            for source, owners in sorted(colliding.items())
        )
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: runtime serializer path "
            f"{location!r} has multiple writable fields binding one source: {detail}. DRF "
            "would silently discard one validated value. Give every runtime writable field a "
            "distinct source.",
        )

    for spec in specs:
        if spec.kind not in (NESTED_SINGLE, NESTED_MULTI):
            continue
        runtime = serializer.fields[spec.target_name]
        child_serializer, many = nested_serializer_child(runtime)
        raw_child = data.get(spec.target_name)
        child_values = raw_child if many and isinstance(raw_child, (list, tuple)) else [raw_child]
        child_mappings = [value for value in child_values if isinstance(value, Mapping)]
        if not child_mappings:
            child_mappings = [{}]
        child_data = {key: value for item in child_mappings for key, value in item.items()}
        child_path = f"{path}.{spec.target_name}" if path else spec.target_name
        _assert_runtime_write_source_ownership(
            mutation_cls,
            child_serializer,
            child_data,
            list(spec.nested_specs),
            path=child_path,
        )


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

    For every relation the schema recorded (``_input_field_specs`` AND the
    ``Meta.injected_fields`` specs, ``_injected_field_specs``), narrow the runtime
    serializer field's ``queryset`` (``PrimaryKeyRelatedField``) / ``child_relation.queryset``
    (``ManyRelatedField``) to ``original.filter(pk__in=<visibility queryset>)`` - the author's
    OWN queryset restriction AND-ed with the related primary ``DjangoType``'s visibility-scoped
    ``get_queryset``. Visibility is an ADDITIONAL constraint, never a replacement (rev6 rev2 P1):
    the earlier version REASSIGNED the field queryset, which erased a serializer author's
    intentional ``PrimaryKeyRelatedField(queryset=Branch.objects.filter(city="allowed"))`` and
    could admit a visible-but-serializer-disallowed row. Composing preserves the author's
    contract while still ensuring DRF's own ``is_valid()`` lookup can never re-fetch a row the
    visibility check hid (a single ``pk__in`` subquery - no extra round trip). A relation whose
    target has no registered primary (a raw-pk relation with no visibility contract) keeps the
    author's own restriction but is STILL pinned to the write alias (and locked when the
    operation locks). The agreement guard already ran, so every relation spec has a matching
    writable runtime field over the recorded model (with a non-``None`` queryset).
    The rewrite is deliberately applied to ``serializer.fields``, whose declared fields DRF
    deep-copies for each serializer instance, never to the serializer class's shared
    ``_declared_fields``. Concurrent requests therefore receive independently scoped relation
    fields. The synchronized regression
    ``tests/rest_framework/test_resolvers.py::test_relation_queryset_scope_is_isolated_between_concurrent_serializer_instances``
    pins that DRF instance-isolation contract with requests carrying different visibility scopes.

    **Nested recursion (rev6 #17).** A nested serializer field's OWN relation fields are scoped
    too, by recursing into the runtime nested serializer's ``.fields`` with the nested reverse
    map (``spec.nested_specs``) - so DRF's nested ``is_valid()`` lookup is the visibility lookup
    at every depth, the same defense-in-depth the top level gets.
    """
    # Injected fields (``Meta.injected_fields``) are relation-capable too: their values reach
    # DRF's SAME second lookup, so their querysets need the SAME pin + visibility + lock
    # discipline as the GraphQL-input relations (the specs are disjoint by class validation).
    _scope_specs_over_serializer(
        [*mutation_cls._input_field_specs, *(mutation_cls._injected_field_specs or [])],
        serializer,
        info,
    )


def _pin_validator_querysets(serializer: Any, alias: str, *, path: str = "") -> None:
    """Recursively pin every queryset-backed DRF validator to the write alias.

    DRF uniqueness validators perform database reads during ``is_valid()``. Field
    ``UniqueValidator`` instances, serializer-level unique-together/date validators,
    and their nested-serializer counterparts must therefore share the transaction's
    alias. DRF intentionally shares validator objects while copying serializer fields,
    so every queryset-backed validator is shallow-copied and replaced on this serializer
    instance before its queryset is pinned. Filters and validator semantics remain intact,
    while concurrent requests cannot rewrite one another's validator routing.
    """

    def _pinned(validators: Any, owner: str) -> list[Any]:
        pinned = []
        for validator in validators:
            queryset = getattr(validator, "queryset", None)
            if queryset is None:
                pinned.append(validator)
                continue
            local_validator = copy.copy(validator)
            local_validator.queryset = pin_write_queryset(
                queryset.all(),
                alias,
                owner=f"{owner} {type(validator).__name__} queryset",
            )
            pinned.append(local_validator)
        return pinned

    serializer_name = type(serializer).__name__

    def _pin_field(field: serializers.Field, field_path: str) -> None:
        field.validators = _pinned(field.validators, f"{serializer_name}.{field_path}")
        if isinstance(field, serializers.ListSerializer):
            _pin_validator_querysets(field.child, alias, path=field_path)
            return
        if isinstance(field, serializers.BaseSerializer):
            _pin_validator_querysets(field, alias, path=field_path)
            return
        child = getattr(field, "child", None)
        if isinstance(child, serializers.Field):
            _pin_field(child, f"{field_path}.child")
        child_relation = getattr(field, "child_relation", None)
        if isinstance(child_relation, serializers.Field):
            _pin_field(child_relation, f"{field_path}.child_relation")

    owner = f"{serializer_name}{f'.{path}' if path else ''}"
    serializer.validators = _pinned(serializer.validators, owner)
    for field_name, field in serializer.fields.items():
        field_path = f"{path}.{field_name}" if path else field_name
        _pin_field(field, field_path)


def _scope_specs_over_serializer(specs: list, serializer: Any, info: Any) -> None:
    """Scope one serializer's relation-field querysets to visibility, recursing into nested (rev6 #3 / #17).

    The per-serializer body of ``_scope_relation_querysets_to_visibility``, factored out so it
    serves both the top-level input specs and each nested serializer's specs. A relation field's
    final queryset is **author queryset AND target visibility, pinned to the write alias, and
    locked when ``Meta.select_for_update`` locks** (the hardening pass):

    - the author's queryset (an intentional ``PrimaryKeyRelatedField(queryset=...)``
      restriction) stays the base contract, PINNED to the pipeline's write alias - an author
      queryset EXPLICITLY routed to a different alias (``.using("other")``) fails closed
      BEFORE validation (``pin_write_queryset``), never a lookup outside the transaction;
    - the related primary type's visibility queryset is AND-ed on as a ``pk__in`` subquery
      (never a replacement); a raw-pk relation with no registered primary has no visibility
      contract but is STILL pinned (and locked) - DRF's own ``is_valid()`` lookup must run
      inside the same transaction on the same alias regardless;
    - when the operation locks, the composed queryset is reduced to a pk subquery under a
      base-manager ``SELECT ... FOR UPDATE`` (``base_locked_queryset`` - never
      ``select_for_update()`` on the author's arbitrary queryset shape), so the row DRF's
      second relation lookup confirms cannot be deleted out from under the write.

    A nested field recurses into the runtime nested serializer's own fields with the nested
    reverse map, so every depth gets the same pin + visibility + lock discipline.
    """
    pipeline = require_write_pipeline()
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
        field = serializer.fields.get(spec.target_name)
        if field is None:  # pragma: no cover - the agreement guard already required it.
            continue
        relation = (
            field.child_relation if isinstance(field, serializers.ManyRelatedField) else field
        )
        # ``.all()`` normalizes a Manager to a QuerySet (preserving an explicit ``.using``);
        # the pin fails closed on a cross-alias author queryset BEFORE any validation runs.
        scoped = pin_write_queryset(
            relation.queryset.all(),
            pipeline.alias,
            owner=(f"{type(serializer).__name__}.{spec.target_name} relation queryset"),
        )
        # ``related_visibility_queryset`` single-sites the ``registry.get`` resolve +
        # the visibility-scoping call (spec-039 Md3); ``None`` = raw-pk relation with
        # no primary type (no visibility contract to AND on - the pin + lock still apply).
        visible = related_visibility_queryset(
            spec.related_model,
            info,
            _SERIALIZER_ASYNC_RECOURSE,
        )
        if visible is not None:
            # Compose (AND), not replace: keep the author's queryset as the base contract and
            # add visibility as a pk__in constraint (a subquery, so still one lookup per field).
            scoped = scoped.filter(
                pk__in=pin_write_queryset(visible, pipeline.alias).values("pk"),
            )
        if pipeline.lock:
            scoped = base_locked_queryset(spec.related_model, pipeline.alias, scoped)
        relation.queryset = scoped


def _assert_injected_field_agreement(mutation_cls: type, serializer: Any) -> None:
    """Verify each ``Meta.injected_fields`` is runtime-ACCEPTED (rev6 #2 / rev2 P1).

    ``Meta.injected_fields`` names the (narrowed-away) required schema-time fields
    ``get_serializer_injected_data`` supplies. The framework builds the serializer data itself
    (client data + the exact-match injection), so presence is guaranteed by construction - but
    the RUNTIME serializer must still declare each injected field, writable, with the same
    source / kind / relation-model the schema-time field had; otherwise DRF drops or ignores
    the injected value and the required field is silently missing. So each injected field runs
    the SAME per-field agreement check input fields get (using the schema-time
    ``_injected_field_specs`` stashed at bind). A declared-but-unaccepted injected field is a
    clear ``ConfigurationError``.
    """
    if not mutation_cls._mutation_meta.injected_fields:
        return
    for spec in mutation_cls._injected_field_specs:
        # Same present / writable / source / kind / relation-model checks as an input field:
        # the runtime serializer must actually be able to VALIDATE + SAVE the injected value.
        _assert_field_agreement(mutation_cls, serializer, spec)


def _assert_save_kwargs_no_shadow(
    mutation_cls: type,
    serializer: Any,
    save_kwargs: dict[str, Any],
) -> None:
    """Raise if a ``get_serializer_save_kwargs`` key shadows a validated-data key (rev6 #12).

    DRF merges save kwargs over ``serializer.validated_data``, so a colliding save kwarg
    silently replaces the VALIDATED value. The collision check runs against the ACTUAL
    top-level ``validated_data`` keys (available because the check runs after ``is_valid()``),
    not a reconstruction from the input specs - so it covers every way a key can reach
    ``validated_data``: a renamed input (``source=``), a ``Meta.injected_fields`` injection, a
    serializer default, and a ``HiddenField``. Save kwargs are for server-side data OUTSIDE the
    validated payload.
    """
    shadowed = sorted(set(save_kwargs) & set(serializer.validated_data))
    if shadowed:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_save_kwargs returned "
            f"kwarg(s) {shadowed!r} that shadow key(s) in the serializer's validated_data; DRF "
            "merges save kwargs over validated_data, so the value would silently replace the "
            "validated one (client input, injection, default, or hidden field). Save kwargs are "
            "for server-side data outside the validated payload (rename them, or drop the "
            "colliding field).",
        )


@contextmanager
def _write_witness(
    mutation_cls: type,
    model: type,
    alias: str,
) -> Iterator[list[tuple[Any, Any, bool, str | None]]]:
    """Observe + police the ORM writes of the consumer-controlled write phase (the hardening pass).

    Two guards scoped to the write phase (hooks, validation, and ``serializer.save()``),
    on THIS thread only (concurrent requests in other threads are untouched - each request
    installs its own witness):

    - a ``pre_save`` guard over EVERY model: a cross-alias ``Model.save()`` gets a clear,
      early, serializer-specific error naming ``context['write_alias']`` (before Django
      even opens the cross-alias connection). The COMPLETE cross-alias enforcement is the
      pipeline skeleton's ``pipeline_alias_guard`` (``utils/write_transaction.py``): it
      spans every consumer-reachable phase - not just the write step - and rejects EVERY
      statement on a non-pinned connection without attempting to classify reads vs writes
      (lexical classification is bypassable via comments, ``EXPLAIN ANALYZE``, and
      write-capable functions), so signal-less paths (``QuerySet.update()``,
      ``bulk_create``, raw cursor SQL) are covered there;
    - a ``post_save`` recorder for the mutation's backing model: the yielded list collects
      ``(instance, pk_at_write, created, using)`` for every row the ORM actually wrote.
      The pk is SNAPSHOTTED at the signal because the model object is mutable - custom
      code could re-point ``instance.pk`` at a hidden row after a legitimate insert, so
      identity alone (``row is saved``) is forgeable; the saved-result validation compares
      the snapshot. ``serializer.instance`` identity alone is likewise forgeable through
      normal DRF bookkeeping (a custom ``create()`` returning an EXISTING row still gets
      assigned to ``self.instance``); only the observed INSERT + pk snapshot proves the
      returned row is new.

    Signal-less SAME-alias bulk writes are invisible to the recorder; for the create
    witness that fails CLOSED (an unwitnessed create result is rejected - persist the
    returned row via ``instance.save()``). Cross-alias writes cannot hide the same way:
    the pipeline's statement guard sees them regardless of signals.
    """
    owner = threading.get_ident()
    written: list[tuple[Any, Any, bool, str | None]] = []

    def _block_cross_alias(sender: Any, using: Any, **kwargs: Any) -> None:
        if threading.get_ident() != owner:
            return
        if using != alias:
            raise ConfigurationError(
                f"SerializerMutation {mutation_cls.__name__}: the serializer write phase "
                f"attempted to save a {sender.__name__} row on database alias {using!r}, but "
                f"the mutation's transaction is pinned to {alias!r}; a write outside the "
                "pinned alias would escape the transaction (it could not be rolled back with "
                "the mutation). Route the custom save through context['write_alias'].",
            )

    def _record(sender: Any, instance: Any, created: bool, using: Any, **kwargs: Any) -> None:
        del sender, kwargs
        if threading.get_ident() != owner:
            return
        written.append(
            (
                instance,
                instance.pk,
                created,
                using,
            ),
        )

    pre_save.connect(_block_cross_alias, weak=False)
    post_save.connect(_record, sender=model, weak=False)
    try:
        yield written
    finally:
        post_save.disconnect(_record, sender=model)
        pre_save.disconnect(_block_cross_alias)


def _checked_saved_result(
    mutation_cls: type,
    serializer: Any,
    saved: Any,
    authorized_pk: Any,
    alias: str,
    written: list[tuple[Any, Any, bool, str | None]],
) -> Any:
    """Validate the ``serializer.save()`` result before the pipeline trusts it (the hardening pass).

    The re-fetch, the payload, and (on update) the whole authorization story key off the saved
    object, so a custom ``save()`` / ``create()`` / ``update()`` whose return drifted is a
    configuration bug surfaced BEFORE the re-fetch can launder it into a plausible payload:

    - the result must be an instance of the mutation's backing model (a wrong-model return
      would re-fetch some other table's row by coincidental pk);
    - it must be ``serializer.instance`` - DRF's ``save()`` contract assigns the written row
      to ``self.instance`` and returns it; a fabricated object returned WITHOUT going through
      that bookkeeping (a spoofed ``pk`` + hand-set ``_state``) fails closed here even when
      its per-attribute state looks saved;
    - it must carry a non-null pk AND not be ``_state.adding`` (an unsaved instance has
      nothing to re-fetch, and a never-persisted instance with a SPOOFED pk would falsely
      report an update or launder an existing row through the re-fetch);
    - it must live EXACTLY on the pipeline's write alias (``_state.db == alias`` - a
      ``None`` alias means never loaded/saved through the ORM, a different alias means the
      write escaped the transaction; both fail closed, mirroring
      ``check_instance_write_alias``);
    - on UPDATE (``authorized_pk`` is not ``None``) its pk must equal ``authorized_pk`` -
      an IMMUTABLE snapshot captured BEFORE any consumer hook ran. Comparing against the
      live ``instance.pk`` would be forgeable: ``instance`` and ``saved`` can be the same
      mutable object, so a custom ``update()`` re-pointing ``instance.pk`` at a hidden
      row's pk would make the live comparison compare the new pk to itself;
    - on CREATE it must match a witnessed ``created=True`` ORM write on the pinned alias
      (the ``_write_witness`` ``post_save`` record) BY PK SNAPSHOT, not just identity -
      ``serializer.instance`` identity is forgeable through normal DRF bookkeeping (a
      custom ``create()`` returning an existing row is still assigned to
      ``self.instance``), and object identity alone is forgeable too (insert a row, then
      re-point the same object's pk at a hidden row). Only the observed INSERT whose
      snapshotted pk still equals ``saved.pk`` proves the returned row is the new one.
      A custom ``create()`` that persists via signal-less bulk paths fails closed here;
      persist the returned row via ``instance.save()``.
    """
    model = mutation_cls._mutation_meta.model
    name = type(serializer).__name__
    if not isinstance(saved, model):
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: {name}.save() returned {saved!r}, not "
            f"a {model.__name__} instance; the serializer's create()/update() must return the "
            "written model row.",
        )
    if saved is not serializer.instance:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: {name}.save() returned a "
            f"{model.__name__} that is not serializer.instance; DRF's save() assigns the "
            "written row to self.instance and returns it, so a detached return object was "
            "never written through the serializer (a spoofed saved-looking instance would "
            "launder some other row through the re-fetch).",
        )
    if saved.pk is None or saved._state.adding:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: {name}.save() returned an unsaved "
            f"{model.__name__} (pk={saved.pk!r}, adding={saved._state.adding!r}); the "
            "serializer's create()/update() must persist and return the written row - a "
            "never-persisted instance with a spoofed pk would launder an existing row "
            "through the re-fetch.",
        )
    saved_alias = saved._state.db
    if saved_alias != alias:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: {name}.save() returned a row on "
            f"database alias {saved_alias!r}, but the mutation's transaction is pinned to "
            f"{alias!r}; a write outside the pinned alias escapes the transaction. Route the "
            "custom save through context['write_alias'].",
        )
    if authorized_pk is not None and str(saved.pk) != str(authorized_pk):
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: {name}.save() returned "
            f"{model.__name__} pk={saved.pk!r}, but the located, authorized row is "
            f"pk={authorized_pk!r}; an update must write the row that was authorized, never "
            "a substituted one.",
        )
    matching_write = any(
        row is saved
        and created is (authorized_pk is None)
        and using == alias
        and str(row_pk) == str(saved.pk)
        for row, row_pk, created, using in written
    )
    if not matching_write:
        action = "INSERTED" if authorized_pk is None else "UPDATED"
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: {name}.save() returned a "
            f"{model.__name__} that was never observed being {action} on alias {alias!r} "
            "during the save; the serializer must persist and return the same row addressed "
            "by this mutation. Returning an existing instance without saving it is not an "
            "update and cannot be reported as success.",
        )
    return saved


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
    reverse_map = _build_reverse_map(mutation_cls._input_field_specs)
    pipeline = require_write_pipeline()
    alias = pipeline.alias
    # The authorized pk is an IMMUTABLE snapshot captured by the pipeline skeleton
    # immediately after the locate - BEFORE the permission hook, the first
    # consumer-controlled code, could touch the mutable located instance (a live
    # ``instance.pk`` read here would already be too late: a malicious permission
    # method runs before this step). A direct (skeleton-less) invocation falls back
    # to snapshotting at step entry - still before any of THIS step's hooks run.
    authorized_pk = pipeline.authorized_pk
    if authorized_pk is None and instance is not None:
        authorized_pk = instance.pk
    # The witness wraps the ENTIRE consumer-controlled phase (the data/kwargs hooks,
    # ``is_valid()`` with its author validators, the save-kwargs hook, and ``save()``):
    # a cross-alias ``Model.save()`` is blocked at ``pre_save`` with a serializer-specific
    # error, and every actual write of the backing model is recorded with a pk snapshot
    # so a create result can be PROVEN inserted. The statement-level cross-alias net
    # (signal-less paths included) is the pipeline skeleton's ``pipeline_alias_guard``,
    # which spans this step and every other consumer-reachable phase.
    witness = _write_witness(mutation_cls, mutation_cls._mutation_meta.model, alias)
    with witness as written:
        return _guarded_serializer_write(
            mutation_cls,
            info,
            instance,
            provided_data,
            serializer_class=serializer_class,
            reverse_map=reverse_map,
            alias=alias,
            authorized_pk=authorized_pk,
            written=written,
        )


def _guarded_serializer_write(
    mutation_cls: type,
    info: Any,
    instance: Any,
    provided_data: dict[str, Any],
    *,
    serializer_class: type,
    reverse_map: dict[str, tuple[str, dict | None]],
    alias: str,
    authorized_pk: Any,
    written: list[tuple[Any, Any, bool, str | None]],
) -> Any | list[FieldError]:
    """The write-step body, run inside the ``_write_witness`` guards (the hardening pass)."""
    # The framework builds the authoritative serializer data ITSELF (the hardening pass):
    # decoded client data + the exact-match ``Meta.injected_fields`` injection - a
    # ``get_serializer_kwargs`` override can no longer replace or extend it.
    injected = _injected_serializer_data(
        mutation_cls,
        info,
        provided_data=provided_data,
        instance=instance,
    )
    final_data = {**provided_data, **injected}
    kwargs = _merged_serializer_kwargs(
        mutation_cls,
        info,
        final_data=final_data,
        instance=instance,
        alias=alias,
    )
    serializer = serializer_class(**kwargs)

    # rev6 #1: PROVE the schema-time field map and the runtime serializer AGREE before
    # ``is_valid()`` runs, so a schema hook that exposed a field the runtime serializer does
    # not actually declare (or declares with a different source / relation target / kind) is a
    # framework CONFIGURATION failure - a clear ``ConfigurationError`` - not a silent
    # DRF-ignores-the-unknown-key ambiguity. The schema hook becomes a verified contract.
    _assert_schema_runtime_agreement(mutation_cls, serializer)
    # rev6 #2: verify the runtime serializer ACCEPTS each ``Meta.injected_fields`` field
    # (present / writable / same source / kind / relation-model), so a declared-but-unaccepted
    # injected field is a clear ConfigurationError, not a silent validation failure.
    _assert_injected_field_agreement(mutation_cls, serializer)
    _assert_runtime_write_source_ownership(
        mutation_cls,
        serializer,
        final_data,
        [*mutation_cls._input_field_specs, *(mutation_cls._injected_field_specs or [])],
    )
    # rev6 #3: adapt each relation field's queryset to the SAME visibility-scoped queryset the
    # decode used - pinned to the write alias and locked when the operation locks - so DRF's
    # own ``is_valid()`` lookup is the VISIBILITY lookup inside the transaction rather than an
    # unscoped second fetch (defense in depth - DRF can never re-fetch a row the decode's
    # visibility check hid, even if the decode is bypassed).
    _scope_relation_querysets_to_visibility(mutation_cls, serializer, info)
    # DRF's queryset-backed validators issue their own database reads during
    # ``is_valid()``. Pin every field-, serializer-, and nested-level validator
    # queryset to the same alias before validation so uniqueness cannot consult
    # another shard or escape the transaction.
    _pin_validator_querysets(serializer, alias)

    if not serializer.is_valid():
        return serializer_errors_to_field_errors(serializer.errors, reverse_map)

    saved: Any = None

    def _do_save() -> None:
        # rev6 #12: the DRF-native ``serializer.save(**kwargs)`` customization point
        # (request-derived save-time data, e.g. ``owner=request.user``), distinct from the
        # constructor ``get_serializer_kwargs``. Rejected if a save kwarg would shadow ANY
        # validated_data key (it would silently override the validated value). Invoked
        # INSIDE this value-preserving closure so a hook-raised DRF / Django
        # ``ValidationError`` (or ``IntegrityError`` from a hook query) rides the SAME
        # error mapping as ``save()`` itself - the ``FieldError`` envelope, never a
        # top-level ``GraphQLError``. The hook receives a recursive plain-container CLONE:
        # ``provided_data`` shares its nested containers (a decoded JSONField value, a
        # nested-input dict) with the ``data`` the serializer validated, so DRF's
        # ``validated_data`` can carry those SAME objects by identity - an in-place
        # mutation in the hook would silently rewrite the validated value.
        nonlocal saved
        save_kwargs = dict(
            mutation_cls().get_serializer_save_kwargs(
                info,
                _plain_container_clone(provided_data),
                instance,
            ),
        )
        _assert_save_kwargs_no_shadow(mutation_cls, serializer, save_kwargs)
        saved = serializer.save(**save_kwargs)

    try:
        write_error = save_or_field_errors(_do_save)
    except DRFValidationError as exc:
        return serializer_errors_to_field_errors(exc.detail, reverse_map)
    except DjangoValidationError as exc:
        return validation_error_to_field_errors(exc)
    if write_error is not None:
        return write_error
    # The saved result is validated BEFORE the pipeline re-fetches / trusts it: correct model,
    # DRF save-bookkeeping identity, non-null pk, pinned alias, witnessed pk-snapshotted
    # INSERT on create, and - on update - the pre-hook authorized-pk snapshot.
    return _checked_saved_result(mutation_cls, serializer, saved, authorized_pk, alias, written)


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


# The serializer async entry, via the shared factory (spec-039 M1a). ONLY the async
# half is taken: the serializer sync entry (``resolve_serializer_sync`` above) is
# bespoke - it calls ``run_write_pipeline_sync`` with decode / write lambdas
# directly, with no ``_run_*_pipeline_sync`` dispatcher to normalize - so the
# generated sync entry is discarded. The async half runs
# ``_run_serializer_pipeline_sync`` through the shared ``run_pipeline_async`` boundary
# (single-sourced with the model + form flavors), so the three flavors cannot drift
# on the boundary contract.
_, resolve_serializer_async = make_resolver_entries(_run_serializer_pipeline_sync)
