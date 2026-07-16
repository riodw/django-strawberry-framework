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

- **Write via ``serializer.save()`` inside a nested-``atomic`` savepoint and the
  pinned-alias write phase, in a value-preserving closure** (the closure captures
  ``saved = serializer.save()`` via ``nonlocal`` - called EXACTLY ONCE). A save
  failure rolls the savepoint back BEFORE the exception converts into the
  envelope, so a custom ``save()`` that wrote rows then raised leaves NO partial
  write. Routing is by exception CLASS (F2 / H2), all caught OUTSIDE the atomic
  block: a DRF ``serializers.ValidationError``'s ``.detail`` -> the recursive
  flattener; a Django ``ValidationError`` -> the flat ``036`` mapper
  (``error_dict`` / ``messages``, NEVER ``.detail``); an ``IntegrityError`` ->
  the shared ``036`` integrity mapper - three separate ``except`` branches (DRF
  first), never a top-level ``GraphQLError``.

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
shared ``036`` integrity mapper, the raw-pk coercion, and the
object-returning ``visible_related_object`` visibility query are all CALLED, not
re-implemented (the spec-039 import manifest). The genuinely net-new code is the
serializer-field-keyed relation decoder and the recursive serializer-error
flattener.
"""

from __future__ import annotations

import copy
import datetime
import decimal
import enum
import fractions
import threading
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from types import MappingProxyType
from typing import Any

import strawberry
from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files import File
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save, pre_save
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from ..exceptions import ConfigurationError
from ..mutations.inputs import NON_FIELD_ERROR_KEY, FieldError
from ..mutations.resolvers import (
    _integrity_error_field_errors as integrity_error_field_errors,
)
from ..mutations.resolvers import (
    make_resolver_entries,
    run_write_pipeline_sync,
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
    assert_no_target_drift,
    base_locked_queryset,
    pin_write_queryset,
    pipeline_write_phase,
    pks_match,
    require_write_pipeline,
)
from ..utils.write_values import (
    decode_provided_fields,
    decode_scalar_leaf,
    decode_visible_relation,
    type_check_relation_id,
)
from .hook_context import SerializerHookContext, UploadMetadata
from .inputs import (
    runtime_validated_data_fields,
    writable_source_collisions,
    writable_star_sources,
)
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

    **Iterative, cycle- and budget-aware** (the hardening pass): the error structure mirrors a
    client-controlled input (a deeply-nested ``JSONField`` payload reproduces its nesting in
    ``serializer.errors`` / a DRF ``ValidationError.detail``), so a recursive walk would let a
    deep payload crash the pipeline with a ``RecursionError`` at the ERROR path - the exact
    availability hole the iterative clone already closes on the data path. The walk is an
    explicit stack; a CYCLIC detail structure (constructible only by author code raising a
    hand-built ``ValidationError``) fails loud as a ``ConfigurationError``; and a node budget
    caps pathological fan-out - when exceeded, the flattened list ends with one ``"__all__"``
    ``truncated`` marker instead of unbounded work.
    """
    children = _error_node_children(errors, reverse_map, prefix)
    if children is None:
        return [_error_leaf(errors, prefix)]
    flattened: list[FieldError] = []
    budget = _ERROR_FLATTEN_NODE_BUDGET
    active: set[int] = {id(errors)}
    frames: list[tuple[Any, Any]] = [(errors, iter(children))]
    while frames:
        node, entries = frames[-1]
        descended = False
        for child, child_map, child_prefix in entries:
            budget -= 1
            if budget < 0:
                flattened.append(
                    field_error(
                        NON_FIELD_ERROR_KEY,
                        "Too many validation error details to report; the list was truncated.",
                        codes="truncated",
                    ),
                )
                return flattened
            grand = _error_node_children(child, child_map, child_prefix)
            if grand is None:
                flattened.append(_error_leaf(child, child_prefix))
                continue
            if id(child) in active:
                raise ConfigurationError(
                    "SerializerMutation validation errors contain a CYCLIC detail structure "
                    "(a dict or list that transitively contains itself); cyclic error details "
                    "cannot be flattened. Break the cycle in the raised ValidationError.",
                )
            active.add(id(child))
            frames.append((child, iter(grand)))
            descended = True
            break
        if not descended:
            active.discard(id(node))
            frames.pop()
    return flattened


# The flattener's node budget: far above any legitimate ``serializer.errors``
# shape (hundreds of fields x nested items), far below pathological fan-out. On
# exhaustion the flattened list ends with one ``"__all__"`` ``truncated`` marker.
_ERROR_FLATTEN_NODE_BUDGET = 10_000


def _error_node_children(
    errors: Any,
    reverse_map: dict[str, tuple[str, dict | None]],
    prefix: str,
) -> list[tuple[Any, Any, str]] | None:
    """Expand one error node into ``(child, child_map, child_prefix)`` entries, or ``None`` for a leaf.

    The single expansion rule the iterative flattener walks: a **dict** re-keys each key to its
    GraphQL name AS IT DESCENDS (not only the root - rev6 #17 review P2) via ``_rekey_segment``
    with the level's own reverse map; a **list containing dicts / lists** indexes each child
    under its numeric position, carrying the SAME level map (the items are the same nested
    serializer; a mixed list never occurs in DRF's shape, but the guard keeps a stray leaf from
    dropping). Anything else - a list of leaf messages, a bare string, an ``ErrorDetail`` - is a
    leaf (``None``).
    """
    if isinstance(errors, dict):
        children: list[tuple[Any, Any, str]] = []
        for key, value in errors.items():
            segment, child_map = _rekey_segment(str(key), reverse_map)
            children.append((value, child_map, join_error_path(prefix, segment)))
        return children
    if isinstance(errors, list) and any(isinstance(item, (dict, list)) for item in errors):
        return [
            (item, reverse_map, join_error_path(prefix, str(index)))
            for index, item in enumerate(errors)
        ]
    return None


def _error_leaf(errors: Any, prefix: str) -> FieldError:
    """Build the shared leaf for one flattened error path.

    A leaf is a list of messages, a bare string, or an ``ErrorDetail``; ``prefix`` is already
    fully re-keyed during descent, so the shared ``field_error`` ctor gets the dotted GraphQL
    path directly - preserving each DRF ``ErrorDetail.code`` alongside the message (rev6 #4)
    and the structured path (rev6 #13, derived inside ``field_error`` from the dotted key).
    """
    return field_error(
        prefix,
        errors,
        codes=_error_detail_codes(errors),
    )


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


def _upload_metadata(item: Any) -> UploadMetadata:
    """Build the frozen upload descriptor a hook data view carries instead of the file.

    The authoritative upload object is STATEFUL (a hook that ``read()``s it would
    exhaust the stream before validation consumes it), so hooks only ever see the
    safe descriptor; the real object stays on the framework-built serializer
    ``data`` for the serializer's own validation.
    """
    try:
        size = item.size
    except Exception:
        size = None
    return UploadMetadata(
        name=getattr(item, "name", None),
        size=size,
        content_type=getattr(item, "content_type", None),
    )


# Leaf value types the frozen hook view may expose BY REFERENCE: each cannot be
# mutated in place, so a hook holding one cannot alter the authoritative data.
# Anything outside this allow-list (and not a frozen container or an upload) is an
# OPAQUE, possibly-mutable leaf - a hook could mutate it and thereby mutate the
# authoritative ``provided_data`` - so the freeze FAILS CLOSED on it rather than
# promising an immutable view it cannot deliver. ``datetime`` covers ``date`` by
# subclass; ``bytearray`` is handled separately (rendered as immutable ``bytes``).
_IMMUTABLE_LEAF_TYPES: tuple[type, ...] = (
    str,
    bytes,
    bool,
    int,
    float,
    complex,
    type(None),
    decimal.Decimal,
    fractions.Fraction,
    datetime.date,
    datetime.time,
    datetime.timedelta,
    datetime.tzinfo,
    uuid.UUID,
    enum.Enum,
    range,
)

# The container types the frozen view DESCENDS into and renders immutable: a ``dict``
# -> read-only ``MappingProxyType``, a ``list``/``tuple`` -> ``tuple``, a
# ``set``/``frozenset`` -> ``frozenset`` (children frozen at every depth). ``str`` /
# ``bytes`` / ``bytearray`` are deliberately NOT here - they are leaves, not element
# containers - so they are never iterated as structure.
_FROZEN_VIEW_CONTAINERS: tuple[type, ...] = (
    dict,
    list,
    tuple,
    set,
    frozenset,
)


def _frozen_hook_view(value: Any) -> Any:
    """Build the IMMUTABLE view of a decoded data tree the consumer hooks receive.

    The hardened hooks (``get_serializer_injected_data`` / ``get_serializer_kwargs``
    / ``get_serializer_save_kwargs``) must not be able to mutate the authoritative
    serializer data - not the outer mapping, not a nested list, not a mutable scalar
    leaf, not an uploaded file's stream. A mutable clone only prevents the outer
    copies; this goes further and freezes the structure itself: every ``dict`` becomes
    a read-only ``MappingProxyType``, every ``list``/``tuple`` a ``tuple``, every
    ``set``/``frozenset`` a ``frozenset``, every ``bytearray`` immutable ``bytes``, and
    every file object an ``UploadMetadata`` descriptor (the authoritative upload reaches
    only the serializer's validation). Immutable scalar leaves (str / int / Decimal /
    datetime / UUID / ...) pass through by reference. An OPAQUE, possibly-mutable leaf
    (a ``bytearray`` aside, a custom scalar object with no immutable rendering) is NOT
    passed by reference - a hook could mutate it and thereby mutate the authoritative
    data - it FAILS CLOSED with a ``ConfigurationError`` instead of a false promise of
    immutability.

    Iterative (an explicit stack, post-order), NOT recursive: a ``JSONField``
    input is client-controlled and json-parseable nesting easily exceeds Python's
    recursion limit, so a recursive freeze would let a deeply-nested payload crash
    the pipeline with a ``RecursionError`` (an availability hole, not a validation
    error). ``memo`` keeps a SHARED (diamond) reference shared in the view;
    ``active`` tracks the ancestor path so a genuine CYCLE (impossible in parsed
    GraphQL JSON, constructible by a hook) fails loud instead of looping forever.
    """

    def _freeze_leaf(item: Any) -> Any:
        if isinstance(item, File):
            return _upload_metadata(item)
        if isinstance(item, bytearray):
            return bytes(item)
        if isinstance(item, _IMMUTABLE_LEAF_TYPES):
            return item
        raise ConfigurationError(
            "SerializerMutation hook data contains a value of type "
            f"{type(item).__name__!r} that cannot be frozen into an immutable hook view. "
            "The frozen view exposes only immutable scalars, uploads (as UploadMetadata), "
            "and dict/list/tuple/set containers; an opaque, possibly-mutable leaf is "
            "rejected rather than passed by reference (a hook could mutate it and thereby "
            "mutate the authoritative serializer data). Supply a plain JSON-compatible value.",
        )

    if not isinstance(value, _FROZEN_VIEW_CONTAINERS):
        return _freeze_leaf(value)

    def _entries(container: Any) -> Any:
        return (
            iter(container.items()) if isinstance(container, dict) else iter(enumerate(container))
        )

    def _new_acc(container: Any) -> Any:
        return {} if isinstance(container, dict) else []

    def _finalize(source: Any, acc: Any) -> Any:
        if isinstance(source, dict):
            return MappingProxyType(acc)
        if isinstance(source, (set, frozenset)):
            return frozenset(acc)
        return tuple(acc)

    def _place(target: Any, key: Any, child: Any) -> None:
        if isinstance(target, dict):
            target[key] = child
        else:
            target.append(child)

    memo: dict[int, Any] = {}
    active: set[int] = {id(value)}
    # Frame: (source container, its entries iterator, the mutable accumulator the
    # frozen children land in, and the parent accumulator + key the FROZEN result
    # is placed into when this frame pops - ``None`` parent means the root).
    frames: list[tuple[Any, Any, Any, Any, Any]] = [
        (
            value,
            _entries(value),
            _new_acc(value),
            None,
            None,
        ),
    ]
    while frames:
        source, entries, acc, parent_acc, parent_key = frames[-1]
        descended = False
        for key, item in entries:
            if not isinstance(item, _FROZEN_VIEW_CONTAINERS):
                _place(acc, key, _freeze_leaf(item))
                continue
            item_id = id(item)
            if item_id in active:
                raise ConfigurationError(
                    "SerializerMutation hook data contains a CYCLIC container (a dict, list, "
                    "tuple, or set that transitively contains itself); cyclic data cannot be "
                    "frozen or validated. Break the cycle in the hook-supplied structure.",
                )
            frozen_child = memo.get(item_id)
            if frozen_child is not None:
                _place(acc, key, frozen_child)
                continue
            active.add(item_id)
            frames.append(
                (
                    item,
                    _entries(item),
                    _new_acc(item),
                    acc,
                    key,
                ),
            )
            descended = True
            break
        if descended:
            continue
        frames.pop()
        active.discard(id(source))
        frozen = _finalize(source, acc)
        memo[id(source)] = frozen
        if parent_acc is None:
            return frozen
        _place(parent_acc, parent_key, frozen)
    raise AssertionError("unreachable")  # pragma: no cover - the root frame always returns.


def _injected_serializer_data(
    mutation_cls: type,
    info: Any,
    *,
    frozen_provided: Any,
    hook_context: SerializerHookContext,
) -> dict[str, Any]:
    """Collect the ``Meta.injected_fields`` values through ``get_serializer_injected_data``.

    The declared-injection half of the final serializer data (the hardening pass):
    the framework builds the authoritative data itself from the DECODED client data
    plus this hook's return - a ``get_serializer_kwargs`` override can no longer
    replace or extend ``data``. The hook receives the FROZEN view of the decoded
    client data (immutable containers, upload metadata instead of the stateful
    upload objects) plus the frozen ``SerializerHookContext`` - never the live
    located instance - and its returned keys must EXACTLY match
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
            data=frozen_provided,
            hook_context=hook_context,
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
    hook_context: SerializerHookContext,
) -> dict[str, Any]:
    """Construct the serializer kwargs through ``get_serializer_kwargs`` + the framework merge (H3).

    Calls the overridable CONSTRUCTOR-ONLY hook ``get_serializer_kwargs(info,
    data=<frozen view>, hook_context=<frozen context>)`` (the spec D8 step-4
    hook), then OWNS the non-overridable framework rules. ``data``, ``instance``,
    ``partial``, ``context["request"]``, and ``context["write_alias"]`` are
    FRAMEWORK-OWNED:

    - ``data`` is the framework-built final data (decoded client data + declared
      injection); the hook receives the FROZEN view (immutable containers, upload
      metadata - mutation is structurally impossible), and the returned ``data``
      must be either OMITTED or the exact frozen object the hook received
      (identity, checked via an omission sentinel) - anything else, including an
      explicit ``None``, is a ``ConfigurationError`` (the old
      replace-the-decoded-data bypass). Identity rather than equality: a deep
      comparison of two independently built structures would recurse (deep valid
      payloads crash it), and equality cannot see a semantically different
      reordering of exotic mappings.
    - ``instance`` never reaches the hook (it receives the frozen
      ``SerializerHookContext`` carrying ``instance_pk`` instead of the live,
      mutable row), so ANY returned ``instance`` key is a ``ConfigurationError``
      (the old substitute-the-target bypass - row A's authorization must never
      write row B); the framework injects the located, authorized row itself.
    - ``partial`` is injected for an UPDATE (``instance is not None``), never for
      create; a hook that set ``partial`` itself is a ``ConfigurationError``.
    - the override's ``context`` dict is merged, then ``context["request"]`` is set
      UNCONDITIONALLY to the framework request (a DIFFERENT object is a
      ``ConfigurationError``, the SAME object tolerated) and
      ``context["write_alias"]`` to the pipeline's pinned write alias (a
      conflicting value is a ``ConfigurationError``) - so a custom serializer hook
      that queries or defers work can read the ONE alias the transaction covers.
    """
    frozen_data = _frozen_hook_view(final_data)
    kwargs = dict(
        mutation_cls().get_serializer_kwargs(
            info,
            data=frozen_data,
            hook_context=hook_context,
        ),
    )

    # The reserved-key checks use an omission SENTINEL + object IDENTITY, never
    # equality: a deep ``!=`` over two independently built structures recurses
    # (a ~1,500-level valid payload would crash the comparison even though the
    # freeze itself is iterative), and a ``pop(..., None)`` default would make an
    # explicit ``data=None`` indistinguishable from omission. A hook may omit the
    # key or pass back the EXACT frozen object it received (the default's
    # pass-through); anything else fails closed.
    returned_data = kwargs.pop("data", _OMITTED)
    if returned_data is not _OMITTED and returned_data is not frozen_data:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_kwargs returned a "
            "`data` value that is not the exact object the hook received; `data` is "
            "framework-owned (decoded client input plus Meta.injected_fields injection), so "
            "the hook must pass it through unchanged or omit it. Supply extra fields via "
            "get_serializer_injected_data + Meta.injected_fields, not by rewriting `data`.",
        )
    kwargs["data"] = final_data

    if "instance" in kwargs:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_kwargs returned an "
            "`instance` kwarg; `instance` is framework-owned (authorization is point-in-time "
            "against the located row - the framework injects that row itself, and hooks only "
            "see its pk via hook_context.instance_pk). Remove `instance` from the override.",
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
    runtime_sources = {field_name: field.source for field_name, field in runtime_fields.items()}
    location = path or "<root>"
    star_fields = writable_star_sources(runtime_sources)
    if star_fields:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}: runtime serializer path "
            f"{location!r} has writable field(s) {star_fields!r} declaring source='*'. DRF "
            "merges a whole-object field's returned mapping into validated_data, so it can "
            "silently replace client or injected values under any key. Remove the field, make "
            "it read_only, or give it a concrete single-column source.",
        )
    colliding = writable_source_collisions(runtime_sources)
    if colliding:
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
    _scope_specs_over_serializer(_write_surface_specs(mutation_cls), serializer, info)


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


def _assert_save_kwargs_not_model_fields(mutation_cls: type, save_kwargs: dict[str, Any]) -> None:
    """Raise if a ``get_serializer_save_kwargs`` key names ANY model field (the hardening pass).

    DRF merges save kwargs into the write with no validation and no visibility check, so a
    save kwarg naming a model column / relation (``category=<hidden row>``,
    ``owner_id=<pk>``) would be an unaudited model-field injection - exactly the channel
    ``Meta.injected_fields`` + ``get_serializer_injected_data`` exists to make declared,
    validated, and visibility-checked. The validated-data shadow check
    (``_assert_save_kwargs_no_shadow``) only catches keys the client / injection actually
    supplied; this closes the rest: save kwargs may carry ONLY non-model custom arguments
    (the ``serializer.save(notify=True)`` pattern a custom ``create()``/``update()``
    consumes).
    """
    if not save_kwargs:
        return
    model = mutation_cls._mutation_meta.model
    field_names: set[str] = set()
    for field in model._meta.get_fields():
        field_names.add(field.name)
        attname = getattr(field, "attname", None)
        if attname:
            field_names.add(attname)
    offenders = sorted(set(save_kwargs) & field_names)
    if offenders:
        raise ConfigurationError(
            f"SerializerMutation {mutation_cls.__name__}.get_serializer_save_kwargs returned "
            f"kwarg(s) {offenders!r} that name {model.__name__} model field(s); a save kwarg "
            "bypasses validation and visibility, so model-field injection must go through "
            "Meta.injected_fields + get_serializer_injected_data instead. Save kwargs may "
            "only carry non-model custom arguments.",
        )


def _write_surface_specs(mutation_cls: type) -> list:
    """Return the top-level write-surface specs: GraphQL input fields + ``Meta.injected_fields``.

    The one list every top-level per-field discipline walks (queryset scoping, the
    relation-intent ledger, the M2M snapshot, the post-save attestation): the two spec sets
    are disjoint by class validation, so concatenation is exact.
    """
    return [*mutation_cls._input_field_specs, *(mutation_cls._injected_field_specs or [])]


class _RelationIntentLedger:
    """The per-write record of the EXACT objects each relation field resolved (hardening pass).

    ``records`` maps a dotted spec path (``category`` / ``shelves.branch``) to the ordered
    list of values that field's ``run_validation()`` returned - one entry per call, so a
    nested ``many=True`` child (whose ONE field instance validates every list item) records
    one entry per item, in item order. ``consume`` reads the entries back in the same order
    during the post-``is_valid()`` identity walk; ``counters`` keeps nested items aligned.
    """

    __slots__ = ("counters", "records")

    def __init__(self) -> None:
        self.records: dict[str, list[Any]] = {}
        self.counters: dict[str, int] = {}

    def record(self, path: str, value: Any) -> None:
        self.records.setdefault(path, []).append(value)

    def consume(self, path: str) -> Any:
        """Return the next recorded value for ``path``, or ``_OMITTED`` when none is pending."""
        index = self.counters.get(path, 0)
        entries = self.records.get(path)
        if entries is None or index >= len(entries):
            return _OMITTED
        self.counters[path] = index + 1
        return entries[index]

    def assert_fully_consumed(self, mutation_cls: type) -> None:
        """Every recorded relation resolution must have been consumed by the intent walk.

        A record left unconsumed means a relation field validated (resolving a
        visibility-scoped object) but its value never reached the compared
        ``validated_data`` - a parent / list validator nulled the nested value,
        removed it, or dropped list items, silently discarding the client's
        relation intent. The direct top-level pop is caught inline in the walk;
        this backstop catches the NESTED and dropped-list-item cases the recursion
        skips (it cannot recurse into a value that is gone). Fail closed.
        """
        for path, entries in self.records.items():
            if self.counters.get(path, 0) != len(entries):
                raise ConfigurationError(
                    f"SerializerMutation {mutation_cls.__name__}: relation {path!r} was "
                    "supplied by the client and resolved by the field, then removed from "
                    "validated_data before the write (a nested value was nulled or dropped, "
                    "or list items were removed); the client's relation intent would be "
                    "silently discarded. Validators may reject a supplied relation, never "
                    "drop it.",
                )


def _relation_object_identity(obj: Any) -> tuple:
    """Immutable ``(object, pk, alias)`` capture of one resolved relation row.

    The pk and database alias are copied out BY VALUE at ``run_validation`` time
    (immutable primitives), alongside the object reference the identity check
    needs. ``(None, None, None)`` for a null relation.
    """
    if obj is None:
        return (None, None, None)
    state = getattr(obj, "_state", None)
    return (obj, getattr(obj, "pk", None), getattr(state, "db", None))


def _relation_intent_snapshot(value: Any) -> Any:
    """Snapshot what a relation field's ``run_validation`` resolved, immutably.

    Captured BEFORE any object-level validator runs (the ledger records at field
    ``run_validation`` time), so a validator that mutates a resolved relation
    object's ``pk`` / ``_state.db`` IN PLACE - leaving object identity intact, so
    a bare ``is`` check would miss it - is caught by the post-``is_valid()``
    comparison against these captured primitives. A list relation snapshots one
    ``(object, pk, alias)`` tuple per row, in order.
    """
    if isinstance(value, list):
        return [_relation_object_identity(item) for item in value]
    return _relation_object_identity(value)


def _relation_identity_intact(value: Any, snapshot: tuple) -> bool:
    """``value`` must BE the recorded object AND still carry its recorded pk + alias."""
    recorded_obj, recorded_pk, recorded_db = snapshot
    if value is not recorded_obj:
        return False
    if value is None:
        return recorded_pk is None and recorded_db is None
    state = getattr(value, "_state", None)
    return getattr(value, "pk", None) == recorded_pk and getattr(state, "db", None) == recorded_db


def _instrument_relation_intent(mutation_cls: type, serializer: Any) -> _RelationIntentLedger:
    """Wrap every (top-level and nested) relation field's ``run_validation`` to record its return.

    Installed AFTER the queryset scoping (the recorded objects are the visibility-scoped,
    alias-pinned resolutions) and BEFORE ``is_valid()`` - so the record is what DRF's OWN
    field produced, captured before any field-level or object-level validator could replace
    it. The wrap is applied to the per-instance field objects (DRF deep-copies declared
    fields per serializer instance), never to shared class state; a custom
    ``PrimaryKeyRelatedField.pk_field`` stays fully supported - whatever transformation it
    applies, the ledger records the RELATION OBJECT the field finally resolved, which is the
    identity the intent walk and the attestation verify.
    """
    ledger = _RelationIntentLedger()
    _instrument_intent_specs(mutation_cls._input_field_specs, serializer, ledger, path="")
    _instrument_intent_specs(
        mutation_cls._injected_field_specs or [],
        serializer,
        ledger,
        path="",
    )
    return ledger


def _instrument_intent_specs(
    specs: list,
    serializer: Any,
    ledger: _RelationIntentLedger,
    *,
    path: str,
) -> None:
    """Instrument one serializer level's relation fields, recursing into nested serializers."""
    for spec in specs:
        field = serializer.fields.get(spec.target_name)
        if field is None:  # pragma: no cover - the agreement guard already required it.
            continue
        field_path = join_error_path(path, spec.target_name)
        if spec.kind in (NESTED_SINGLE, NESTED_MULTI):
            child_serializer, _many = nested_serializer_child(field)
            _instrument_intent_specs(
                spec.nested_specs,
                child_serializer,
                ledger,
                path=field_path,
            )
            continue
        if spec.kind not in (RELATION_SINGLE, RELATION_MULTI):
            continue
        _record_field_intent(field, ledger, field_path)


def _record_field_intent(field: Any, ledger: _RelationIntentLedger, path: str) -> None:
    """Shadow ``field.run_validation`` with a recording wrapper (per-instance, never shared)."""
    original = field.run_validation

    def _recording(data: Any = serializers.empty) -> Any:
        value = original(data)
        ledger.record(path, _relation_intent_snapshot(value))
        return value

    field.run_validation = _recording


def _assert_relation_intent(
    mutation_cls: type,
    serializer: Any,
    ledger: _RelationIntentLedger,
) -> dict[str, Any]:
    """Prove ``validated_data`` still carries the ledger-recorded relation objects BY IDENTITY.

    Runs immediately after ``is_valid()``: for every relation the write surface knows -
    renamed sources (compared under the runtime field's ``source``), ``Meta.injected_fields``
    relations, single relations, lists (length + pairwise identity, so DRF's duplicate and
    explicit-empty-list semantics pass through untouched), and nested paths (each list item
    consumes its own record, in item order) - the value in the final ``validated_data`` must
    be the EXACT object (or exact object list) the field's ``run_validation`` produced AND
    still carry the pk + database alias captured at that moment. A field-level or
    object-level validator that REPLACED a resolved row (the hidden-row-substitution attack:
    resolve visible row A, swap in hidden row B) fails closed; one that MUTATED a resolved
    object's pk / alias in place (identity intact) fails closed on the captured-primitive
    comparison; one that POPPED a supplied relation fails closed (silently dropping explicit
    client intent is not allowed - only rejection is); one that INJECTED a relation value the
    field never produced fails closed too. A relation the client never sent produces no
    record and is left to omitted semantics (the omitted-M2M attestation still holds).

    Returns the post-save attestation manifest: for each TOP-LEVEL relation source the
    client supplied, the CANONICAL pk (single, or ``None`` for a null relation) or frozenset
    of pks (multi) CAPTURED at ``run_validation`` time - immutable primitives, not live
    objects. ``_attest_saved_relations`` compares the saved database state against these, so
    a custom ``save()`` that mutates a validated relation object's pk in place cannot forge
    both the database value and the expected value from the same mutable object.
    """
    manifest: dict[str, Any] = {}
    _assert_intent_specs(
        mutation_cls,
        _write_surface_specs(mutation_cls),
        serializer,
        serializer.validated_data,
        ledger,
        path="",
        manifest=manifest,
    )
    # Every recorded relation must have been consumed: an unconsumed record is a
    # relation whose validated value was removed before the write (the nested /
    # list-item pop the inline direct-pop guard cannot see).
    ledger.assert_fully_consumed(mutation_cls)
    return manifest


def _assert_intent_specs(
    mutation_cls: type,
    specs: list,
    serializer: Any,
    validated_data: Any,
    ledger: _RelationIntentLedger,
    *,
    path: str,
    manifest: dict[str, Any],
) -> None:
    """The per-level body of the intent walk (one serializer level, recursing into nested).

    Populates ``manifest`` at the TOP level only (``path == ""``): the captured canonical
    pk(s) per supplied relation source, for the post-save attestation.
    """
    if not isinstance(validated_data, dict):  # pragma: no cover - DRF yields dicts here.
        return
    for spec in specs:
        field = serializer.fields.get(spec.target_name)
        if field is None:  # pragma: no cover - the agreement guard already required it.
            continue
        source = field.source or spec.target_name
        field_path = join_error_path(path, spec.target_name)
        if spec.kind in (NESTED_SINGLE, NESTED_MULTI):
            value = validated_data.get(source)
            if value is None:
                continue
            child_serializer, _many = nested_serializer_child(field)
            items = value if spec.kind == NESTED_MULTI else [value]
            for item in items:
                _assert_intent_specs(
                    mutation_cls,
                    spec.nested_specs,
                    child_serializer,
                    item,
                    ledger,
                    path=field_path,
                    manifest=manifest,
                )
            continue
        if spec.kind not in (RELATION_SINGLE, RELATION_MULTI):
            continue
        # Consume in walk order even when the key was popped, so nested list
        # items stay aligned with their own records.
        recorded = ledger.consume(field_path)
        if source not in validated_data:
            if recorded is _OMITTED:
                # Genuinely omitted by the client: the field never validated, so
                # it produced no record - there is no intent to write, nothing to
                # compare (the post-save attestation still holds the
                # omitted-M2M-unchanged line).
                continue
            # The field DID validate (the client supplied the relation), then a
            # validator POPPED it out of validated_data: explicit client intent
            # would be silently discarded (the relation dropped on create, or a
            # replaced relation preserved on update). Fail closed.
            raise ConfigurationError(
                f"SerializerMutation {mutation_cls.__name__}: relation {field_path!r} was "
                "supplied by the client and resolved by the field, then removed from "
                "validated_data by a validator; the client's relation intent would be "
                "silently dropped. Validators may reject a supplied relation, never pop it.",
            )
        value = validated_data[source]
        if recorded is _OMITTED:
            raise ConfigurationError(
                f"SerializerMutation {mutation_cls.__name__}: validated_data carries relation "
                f"{field_path!r} with a value the field's run_validation never produced; a "
                "validator injected a relation object around the visibility-scoped field "
                "lookup. Relation values must come from the field's own validation.",
            )
        if spec.kind == RELATION_SINGLE:
            intact = _relation_identity_intact(value, recorded)
        else:
            intact = (
                isinstance(value, list)
                and isinstance(recorded, list)
                and len(value) == len(recorded)
                and all(
                    _relation_identity_intact(item, expected)
                    for item, expected in zip(value, recorded, strict=True)
                )
            )
        if not intact:
            raise ConfigurationError(
                f"SerializerMutation {mutation_cls.__name__}: validated_data's relation "
                f"{field_path!r} is not the exact object(s) the field's run_validation "
                "resolved; a validator replaced a visibility-checked relation value. "
                "Validators may reject or pop a relation, never substitute it.",
            )
        if path == "":
            # Record the CAPTURED canonical pk(s) for the top-level post-save
            # attestation - immutable primitives from the run_validation snapshot,
            # NOT the live object (whose pk a custom save() could mutate).
            if spec.kind == RELATION_SINGLE:
                manifest[spec.target_name] = recorded[1]
            else:
                manifest[spec.target_name] = frozenset(snap[1] for snap in recorded)


def _m2m_membership_snapshot(
    mutation_cls: type,
    instance: Any,
    alias: str,
) -> dict[str, frozenset]:
    """Snapshot the target's CURRENT memberships for every write-surface direct M2M (update only).

    Taken at write-step entry - strictly AFTER authorization (an unauthorized caller must
    never make the pipeline query relation membership) and BEFORE any consumer hook or the
    save. Scoped to the top-level ``RELATION_MULTI`` specs whose source is a forward
    (writable, direct) M2M on the backing model; the post-save attestation compares an
    OMITTED partial-update M2M against this snapshot to prove a custom ``update()`` left it
    untouched. ``{}`` on create (no memberships exist yet).
    """
    if instance is None:
        return {}
    model = mutation_cls._mutation_meta.model
    snapshot: dict[str, frozenset] = {}
    for spec, model_field, source in _attestable_m2m_fields(mutation_cls, model):
        del spec
        del model_field
        snapshot[source] = frozenset(
            getattr(instance, source).all().using(alias).values_list("pk", flat=True),
        )
    return snapshot


def _attestable_m2m_fields(mutation_cls: type, model: type) -> list[tuple[Any, Any, str]]:
    """Yield ``(spec, model_field, source)`` for each top-level direct-M2M write-surface spec."""
    entries: list[tuple[Any, Any, str]] = []
    for spec in _write_surface_specs(mutation_cls):
        if spec.kind != RELATION_MULTI:
            continue
        source = spec.source or spec.target_name
        try:
            model_field = model._meta.get_field(source)
        except FieldDoesNotExist:
            continue  # A serializer-only relation: nothing on the row to attest.
        if not getattr(model_field, "many_to_many", False) or model_field.auto_created:
            continue
        entries.append((spec, model_field, source))
    return entries


def _attest_saved_relations(
    mutation_cls: type,
    serializer: Any,
    saved: Any,
    *,
    alias: str,
    m2m_before: dict[str, frozenset],
    relation_pks: dict[str, Any],
) -> None:
    """Attest the saved row's TOP-LEVEL FK / OneToOne / M2M database state against the intent.

    Custom ``create()`` / ``update()`` (and custom nested persistence) remain trusted
    application code for arbitrary same-alias behavior - but the RETURNED top-level row is
    attested against the intent-walk's ``relation_pks`` manifest (the CANONICAL pk(s)
    CAPTURED at ``run_validation`` time, keyed by ``spec.target_name``), NOT the live
    ``validated_data`` objects - a custom ``save()`` can mutate a validated object's pk in
    place, forging both the persisted column and a live ``obj.pk`` comparison; the captured
    primitives cannot be mutated after the fact:

    - every supplied FK / OneToOne column must hold the captured target pk (read back from
      the DATABASE in one ``values()`` query), compared canonically through the related pk
      field;
    - every supplied M2M must match the captured pk SET (DRF's ``.set()`` semantics: an
      explicit empty list means cleared, duplicate inputs collapse - set comparison preserves
      exactly those semantics);
    - every OMITTED partial-update M2M on the write surface must equal its pre-save snapshot
      (a custom ``update()`` must not silently rewrite memberships the client never sent).

    A divergence is a loud ``ConfigurationError`` (a configuration/trust failure of the
    consumer's custom write code), never a plausible success payload.
    """
    model = mutation_cls._mutation_meta.model
    name = type(serializer).__name__

    fk_checks: list[tuple[str, Any, Any]] = []
    for spec in _write_surface_specs(mutation_cls):
        if spec.kind != RELATION_SINGLE or spec.target_name not in relation_pks:
            continue
        field = serializer.fields.get(spec.target_name)
        source = (field.source if field is not None and field.source else None) or (
            spec.source or spec.target_name
        )
        try:
            model_field = model._meta.get_field(source)
        except FieldDoesNotExist:
            continue  # A serializer-only relation: nothing on the row to attest.
        if not getattr(model_field, "is_relation", False) or model_field.many_to_many:
            continue
        fk_checks.append((spec.target_name, model_field, relation_pks[spec.target_name]))

    if fk_checks:
        row = (
            model._base_manager.using(alias)
            .values(*[model_field.attname for _, model_field, _ in fk_checks])
            .get(pk=saved.pk)
        )
        for target_name, model_field, expected_pk in fk_checks:
            db_value = row[model_field.attname]
            if expected_pk is None:
                intact = db_value is None
            else:
                intact = db_value is not None and pks_match(
                    model_field.related_model,
                    db_value,
                    expected_pk,
                )
            if not intact:
                raise ConfigurationError(
                    f"SerializerMutation {mutation_cls.__name__}: after {name}.save(), the "
                    f"database column for relation {target_name!r} holds {db_value!r}, not "
                    f"the validated target {expected_pk!r}; the custom "
                    "create()/update() ignored or replaced a validated relation. The saved "
                    "row must reflect the validated intent.",
                )

    m2m_fields = _attestable_m2m_fields(mutation_cls, model)
    for spec, model_field, source in m2m_fields:
        del model_field
        current = frozenset(
            getattr(saved, source).all().using(alias).values_list("pk", flat=True),
        )
        if spec.target_name in relation_pks:
            expected = relation_pks[spec.target_name]
            if current != expected:
                raise ConfigurationError(
                    f"SerializerMutation {mutation_cls.__name__}: after {name}.save(), the "
                    f"M2M relation {spec.target_name!r} holds pk set {sorted(map(str, current))!r}, "
                    f"not the validated set {sorted(map(str, expected))!r}; the custom "
                    "create()/update() ignored or replaced a validated relation set.",
                )
        elif source in m2m_before and current != m2m_before[source]:
            raise ConfigurationError(
                f"SerializerMutation {mutation_cls.__name__}: after {name}.save(), the "
                f"OMITTED partial-update M2M relation {spec.target_name!r} changed from its "
                "pre-save membership; a custom update() must not rewrite memberships the "
                "client never sent.",
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
    # Canonical pk-field equality (``to_python`` both sides), never a ``str()``
    # comparison: a UUID pk stringifies in more than one spelling of the SAME
    # row, and a forged pk of the wrong shape must read as a mismatch.
    if authorized_pk is not None and not pks_match(model, saved.pk, authorized_pk):
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
        and pks_match(model, row_pk, saved.pk)
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
    routes ``serializer.errors`` through the flattener), then writes via a
    value-preserving ``serializer.save()`` closure inside a nested-``atomic``
    savepoint and the pinned-alias write phase (``save()`` called EXACTLY ONCE,
    captured via ``nonlocal``). Returns the saved object (the skeleton re-fetches
    it by pk under the G2 plan) or a ``list[FieldError]`` on a validation / write
    failure - with the savepoint rolled back first, so a failed save leaves no
    partial write.

    A save-time failure routes by exception CLASS (F2 / H2) in THREE separate
    ``except`` branches (DRF first), all caught OUTSIDE the atomic block: a DRF
    ``serializers.ValidationError``'s ``.detail`` -> the recursive flattener; a
    Django ``ValidationError`` -> the flat ``036`` mapper (``error_dict`` /
    ``messages``, never ``.detail``); an ``IntegrityError`` -> the shared ``036``
    integrity mapper - never a top-level ``GraphQLError`` at the write.
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
    # The frozen hook context every consumer hook receives INSTEAD of the live,
    # mutable located instance (the hardening pass): the operation kind, the
    # pinned alias, and the authorized pk snapshot.
    hook_context = SerializerHookContext(
        operation=mutation_cls._mutation_meta.operation,
        write_alias=alias,
        instance_pk=authorized_pk,
    )
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
            hook_context=hook_context,
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
    hook_context: SerializerHookContext,
    written: list[tuple[Any, Any, bool, str | None]],
) -> Any | list[FieldError]:
    """The write-step body, run inside the ``_write_witness`` guards (the hardening pass)."""
    # The pre-save M2M membership snapshot (update only), taken at write-step
    # entry - strictly AFTER authorization (relation membership is data an
    # unauthorized caller must never make the pipeline query) and strictly
    # BEFORE any consumer hook or ``serializer.save()`` could touch it. The
    # post-save attestation proves an OMITTED partial-update M2M field is
    # byte-identical to this snapshot.
    m2m_before = _m2m_membership_snapshot(mutation_cls, instance, alias)
    # The frozen view of the decoded client data the consumer hooks receive
    # (immutable containers; uploads as metadata) - built once, shared by the
    # injected-data and save-kwargs hooks.
    frozen_provided = _frozen_hook_view(provided_data)
    # The framework builds the authoritative serializer data ITSELF (the hardening pass):
    # decoded client data + the exact-match ``Meta.injected_fields`` injection - a
    # ``get_serializer_kwargs`` override can no longer replace or extend it.
    injected = _injected_serializer_data(
        mutation_cls,
        info,
        frozen_provided=frozen_provided,
        hook_context=hook_context,
    )
    final_data = {**provided_data, **injected}
    kwargs = _merged_serializer_kwargs(
        mutation_cls,
        info,
        final_data=final_data,
        instance=instance,
        alias=alias,
        hook_context=hook_context,
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
    # The relation-intent ledger (the hardening pass): record the EXACT objects
    # each relation field's ``run_validation()`` resolves - top-level AND nested -
    # BEFORE field-level or object-level validators get a chance to replace them.
    ledger = _instrument_relation_intent(mutation_cls, serializer)

    if not serializer.is_valid():
        return serializer_errors_to_field_errors(serializer.errors, reverse_map)

    # PROVE the final ``validated_data`` still carries the ledger-recorded objects
    # by IDENTITY (renamed sources, injected fields, single relations, lists, and
    # nested paths alike): a validator that swapped a visible row for a hidden one
    # after the scoped field lookup is a loud ``ConfigurationError``, never a write.
    relation_pks = _assert_relation_intent(mutation_cls, serializer, ledger)

    saved: Any = None

    def _do_save() -> None:
        # rev6 #12: the DRF-native ``serializer.save(**kwargs)`` customization point
        # (request-derived save-time data, e.g. ``owner=request.user``), distinct from the
        # constructor ``get_serializer_kwargs``. Rejected if a save kwarg would shadow ANY
        # validated_data key (it would silently override the validated value) or name ANY
        # model field (model-field injection goes through Meta.injected_fields, the
        # auditable per-field contract - save kwargs are for non-model custom arguments).
        # Invoked INSIDE this value-preserving closure so a hook-raised DRF / Django
        # ``ValidationError`` (or ``IntegrityError`` from a hook query) rides the SAME
        # error mapping as ``save()`` itself - the ``FieldError`` envelope, never a
        # top-level ``GraphQLError``. The hook receives the FROZEN data view; the
        # authoritative structures (whose nested containers DRF's ``validated_data``
        # can carry by identity) are unreachable from hook hands.
        nonlocal saved
        save_kwargs = dict(
            mutation_cls().get_serializer_save_kwargs(
                info,
                data=frozen_provided,
                hook_context=hook_context,
            ),
        )
        _assert_save_kwargs_no_shadow(mutation_cls, serializer, save_kwargs)
        _assert_save_kwargs_not_model_fields(mutation_cls, save_kwargs)
        # The last read-only-phase act: reject in-memory drift of the located
        # target (a permission method / hook / validator that ``setattr``-ed the
        # row would otherwise ride into ``serializer.save()`` as an unvalidated
        # write - DRF's ``update()`` saves the WHOLE instance).
        if instance is not None:
            assert_no_target_drift(f"SerializerMutation {mutation_cls.__name__}", instance)
        # The write phase opens for exactly ``serializer.save()``; everything
        # before this point was database-read-only under the phased alias guard.
        with pipeline_write_phase():
            saved = serializer.save(**save_kwargs)

    # The save runs inside its OWN savepoint (a nested ``atomic`` - the same
    # containment ``forced_save_or_field_errors`` uses), rolled back BEFORE a
    # caught validation / integrity failure is converted into the ``FieldError``
    # envelope: a custom ``save()`` that wrote rows and THEN raised must leave
    # the transaction with NO partial writes at conversion time. The exceptions
    # are caught OUTSIDE the atomic block deliberately - an ``IntegrityError``
    # escaping ``save_base``'s savepoint-less inner atomic flags the connection
    # ``needs_rollback``, and only the enclosing atomic's own savepoint rollback
    # clears that flag; a manual savepoint (or a catch INSIDE the block) would
    # leave the transaction refusing every subsequent statement.
    try:
        with transaction.atomic(using=alias):
            _do_save()
    except DRFValidationError as exc:
        return serializer_errors_to_field_errors(exc.detail, reverse_map)
    except DjangoValidationError as exc:
        return validation_error_to_field_errors(exc)
    except IntegrityError:
        return integrity_error_field_errors()
    # The saved result is validated BEFORE the pipeline re-fetches / trusts it: correct model,
    # DRF save-bookkeeping identity, non-null pk, pinned alias, witnessed pk-snapshotted
    # INSERT on create, and - on update - the pre-hook authorized-pk snapshot.
    saved = _checked_saved_result(mutation_cls, serializer, saved, authorized_pk, alias, written)
    # Post-save relation attestation: the DATABASE state of every top-level
    # FK / OneToOne / M2M the client supplied must match the ledger-verified
    # intent, and an OMITTED partial-update M2M must be unchanged - a custom
    # ``create()`` / ``update()`` that ignored or replaced the validated
    # relations is a loud ``ConfigurationError``, never a plausible payload.
    _attest_saved_relations(
        mutation_cls,
        serializer,
        saved,
        alias=alias,
        m2m_before=m2m_before,
        relation_pks=relation_pks,
    )
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
