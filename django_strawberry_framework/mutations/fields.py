"""``DjangoMutationField`` - the write-side field factory (spec-036 Slice 3).

The write-side sibling of ``connection.py::DjangoConnectionField`` /
``relay.py::DjangoNodeField`` (every root field the package ships is a factory
assigned to a class attribute on an ``@strawberry.type``). Two properties make it
diverge from the read-side factories, both forced by timing, not style:

- **No class-attribute annotation** (spec-036 Decision 5 / Decision 7). The
  read-side factories read a consumer annotation naming a type that already
  exists at import (``DjangoConnection[CategoryType]``); the mutation payload is
  generated at ``finalize_django_types`` phase 2.5, AFTER ``@strawberry.type
  class Mutation`` evaluates its annotations, so there is no importable name to
  annotate with. The consumer writes ``create_item = DjangoMutationField(
  CreateItem)`` with no annotation, and this factory types the field itself via a
  ``strawberry.lazy`` forward-ref to the generated ``<Name>Payload`` on the
  synthesized resolver's return annotation - resolved at schema build, after the
  bind materializes the payload class.
- **Runtime ``in_async_context()`` dispatch only** (spec-036 Decision 8). The
  ``DjangoListField`` async-detection asymmetry is "``is_async_callable``
  construction-time for a consumer ``resolver=`` / ``in_async_context()`` runtime
  for the default generated resolver". A mutation pipeline is package-owned -
  there is NO consumer ``resolver=`` seam to inspect at construction - so only the
  runtime half applies: the single synthesized resolver dispatches per call via
  ``in_async_context()`` (mirroring ``relay.py::DjangoNodesField._resolve``), so
  one factory output works under both ``schema.execute_sync`` and ``await
  schema.execute``.

The per-operation argument signature is ``data: <Model>Input!`` (create), ``id``
+ ``data: <Model>PartialInput!`` (update), ``id`` only (delete) - spec-036
Decision 14. The ``id`` argument is the raw ``strawberry.ID`` string (the
``DjangoNodeField`` server-side-decode precedent, ``relay.py`` line 287): the
package decodes / coerces it server-side, so malformed ids reach the resolver
rather than being rejected by Strawberry's argument conversion. The SDL therefore
renders ``id: ID!`` rather than the headline ``id: GlobalID!``; the difference is
cosmetic for the wire contract (the node field shipped the same way) and is not a
defect.

Fallback (NOT implemented - spec-036 Decision 5 / Risks): if Strawberry rejects a
resolver-typed field assigned with no class annotation, the documented fallback is
a ``.field()`` classmethod (``create_item = CreateItem.field()``, graphene-django's
shape). This module ships the PRIMARY no-annotation form; if the schema build
rejects it, that is surfaced to Worker 1 (not silently swapped).
"""

from __future__ import annotations

import inspect
from typing import Annotated, Any

import strawberry
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from ..exceptions import ConfigurationError
from .inputs import (
    CREATE,
    INPUTS_MODULE_PATH,
    editable_input_fields,
    mutation_input_type_name,
)
from .resolvers import resolve_mutation_async, resolve_mutation_sync
from .sets import _OPERATION_INPUT_KIND, DjangoMutation


def _validate_mutation_target(mutation_cls: Any) -> None:
    """Reject a bad ``DjangoMutationField`` target at the construction line (spec-036 Decision 5).

    The target must be a **concrete, validated** ``DjangoMutation`` subclass: a
    class (not an instance / arbitrary value), a ``DjangoMutation`` subclass, and
    carrying a non-``None`` ``_mutation_meta`` (the metaclass stamps it at class
    creation for a concrete subclass; the abstract base carries ``None``). It does
    NOT require ``_input_class`` / ``_payload_type_name`` - those are BIND outputs
    populated at ``finalize_django_types``, and the field is constructed at import
    (when ``@strawberry.type class Mutation`` evaluates) BEFORE the bind runs.
    A failure raises ``ConfigurationError`` naming ``DjangoMutationField`` so the
    error fires at the assignment line, not at finalize.
    """
    if not isinstance(mutation_cls, type) or not issubclass(mutation_cls, DjangoMutation):
        raise ConfigurationError(
            f"DjangoMutationField requires a concrete DjangoMutation subclass; "
            f"got {mutation_cls!r}.",
        )
    if getattr(mutation_cls, "_mutation_meta", None) is None:
        raise ConfigurationError(
            f"DjangoMutationField requires a concrete DjangoMutation subclass with a "
            f"nested Meta; {mutation_cls.__name__} is the abstract base (no Meta).",
        )


def _input_type_name(meta: Any) -> str:
    """Return the generated input class name for a create / update mutation (spec-036 Decision 14).

    Mirrors the bind's name choice (``sets.py::_materialize_input_for``): a
    consumer ``input_class`` / ``partial_input_class`` materializes under its own
    ``__name__``; otherwise the generated name is
    ``mutation_input_type_name(...)`` - the canonical ``<Model>Input`` /
    ``<Model>PartialInput`` for the full shape, or a deterministic shape-derived
    name for a narrowed shape. Computed at construction from the same selectors
    the generator uses so the lazy ``data:`` ref names the exact class the bind
    materializes.
    """
    operation_kind = _OPERATION_INPUT_KIND[meta.operation]
    consumer_input = meta.input_class if operation_kind == CREATE else meta.partial_input_class
    if consumer_input is not None:
        return consumer_input.__name__
    effective_field_names = tuple(
        field.name
        for field in editable_input_fields(meta.model, fields=meta.fields, exclude=meta.exclude)
    )
    full_field_names = tuple(field.name for field in editable_input_fields(meta.model))
    return mutation_input_type_name(
        meta.model,
        operation_kind,
        effective_field_names,
        full_field_names=full_field_names,
    )


def _lazy_ref(type_name: str) -> Any:
    """Return ``Annotated[<type_name>, strawberry.lazy(INPUTS_MODULE_PATH)]``.

    The forward-ref shape ``orders/inputs.py`` uses for its generated input
    classes: a string type name resolved through
    ``mutations.inputs.__dict__`` at schema build, after the phase-2.5 bind
    materializes the named class as a module global. Single-sited so the ``data:``
    argument and the payload return annotation use one ref shape.
    """
    return Annotated[type_name, strawberry.lazy(INPUTS_MODULE_PATH)]


def _synthesized_mutation_signature(
    mutation_cls: type,
) -> tuple[inspect.Signature, dict[str, Any]]:
    """Build the per-operation resolver ``__signature__`` + ``__annotations__`` (spec-036 Decision 14 / 7).

    ``root`` / ``info`` are Strawberry-reserved (bound without becoming GraphQL
    args); the operation's GraphQL args follow:

    - ``create``: ``data: <Model>Input!`` (non-null, no default).
    - ``update``: ``id: ID!`` + ``data: <Model>PartialInput!``.
    - ``delete``: ``id: ID!`` only.

    ``data`` is a ``strawberry.lazy`` forward-ref to the generated input class
    (materialized at the bind, after this signature is built at import - the same
    timing hazard as the payload). ``id`` is the raw ``strawberry.ID`` string (the
    ``DjangoNodeField`` server-side-decode precedent). The **return** annotation is
    a ``strawberry.lazy`` forward-ref to the generated ``<Name>Payload`` (non-null
    - the field always returns a payload; the object slot inside is nullable).
    """
    meta = mutation_cls._mutation_meta
    operation = meta.operation

    params: list[inspect.Parameter] = [
        inspect.Parameter("root", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None),
        inspect.Parameter("info", inspect.Parameter.KEYWORD_ONLY, annotation=Info),
    ]
    annotations: dict[str, Any] = {"info": Info}

    if operation in ("update", "delete"):
        params.append(
            inspect.Parameter("id", inspect.Parameter.KEYWORD_ONLY, annotation=strawberry.ID),
        )
        annotations["id"] = strawberry.ID

    if operation in ("create", "update"):
        data_ann = _lazy_ref(_input_type_name(meta))
        params.append(
            inspect.Parameter("data", inspect.Parameter.KEYWORD_ONLY, annotation=data_ann),
        )
        annotations["data"] = data_ann

    return_annotation = _lazy_ref(f"{mutation_cls.__name__}Payload")
    annotations["return"] = return_annotation
    return inspect.Signature(params, return_annotation=return_annotation), annotations


def DjangoMutationField(  # noqa: N802  # PascalCase for the field-factory family (DjangoConnectionField / DjangoNodeField parity)
    mutation_cls: type,
    *,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Any = (),
) -> Any:
    """Expose a ``DjangoMutation`` on the schema's ``Mutation`` type (spec-036 Decision 5).

    The write-side sibling of ``DjangoConnectionField``. Validates the target at
    the construction line (a concrete ``DjangoMutation`` subclass with a bound
    ``_mutation_meta``), synthesizes the per-operation argument signature + the
    lazy ``data:`` / payload-return refs, and returns ``strawberry.field(
    resolver=...)`` - assigned with **no** class-attribute annotation
    (``create_item = DjangoMutationField(CreateItem)``).

    The resolver dispatches sync-vs-async per call via ``in_async_context()`` (the
    runtime half of the ``DjangoListField`` asymmetry; there is no consumer
    ``resolver=`` to inspect at construction), so one factory output works under
    both ``schema.execute_sync`` and ``await schema.execute``.
    """
    _validate_mutation_target(mutation_cls)

    def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:  # noqa: ARG001
        data = kwargs.get("data", strawberry.UNSET)
        node_id = kwargs.get("id", strawberry.UNSET)
        if in_async_context():
            return resolve_mutation_async(mutation_cls, info, data=data, id=node_id)
        return resolve_mutation_sync(mutation_cls, info, data=data, id=node_id)

    signature, annotations = _synthesized_mutation_signature(mutation_cls)
    _resolve.__signature__ = signature
    _resolve.__annotations__ = annotations
    return strawberry.field(
        resolver=_resolve,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
