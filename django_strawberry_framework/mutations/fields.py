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
Decision 14. The ``id`` argument is the raw ``strawberry.ID`` string - the
``node(id: ID!)`` Relay-spec signature the shipped ``DjangoNodeField`` also uses
(``relay.py`` line 287), so the package decodes the GlobalID **server-side**
rather than letting Strawberry's argument conversion own it. The SDL renders
``id: ID!`` by design (the Relay-spec / node-field contract), and the resolver
decodes the id and type-checks it against the mutation's target model -
``resolvers.py::coerce_lookup_id`` returns a ``FieldError`` on ``id`` for a
malformed / unresolvable / wrong-model id, never coercing it to a bare pk
(feedback #1). This is a single, consistent contract (NOT the headline schema's
``id: GlobalID!``, which the spec is reconciled to ``id: ID!`` to match - feedback
#4); the relation ``<field>_id`` inputs, by contrast, ARE typed ``GlobalID`` (the
Relay-Node target's id type), so malformed *relation* ids are a Strawberry
coercion error while a well-formed-but-invalid one is the in-band ``FieldError``.

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
from .inputs import INPUTS_MODULE_PATH


# TODO(spec-040 Slice 1): promote the lazy-ref + signature-attachment idiom below
# into shared field-factory machinery before auth adds fixed factories. Pseudocode:
# move ``_lazy_ref`` itself plus the ``__signature__`` / ``__annotations__``
# assignment into one helper; build the return lazy ref there, derive an
# ``inspect.Signature`` from the fixed field's keyword arguments, then attach both
# signature artifacts to the dispatcher in one place.
# ``login_mutation`` / ``logout_mutation`` / ``current_user`` need the same
# ``__signature__`` / ``__annotations__`` path as ``DjangoMutationField`` because
# their return types materialize at phase 2.5. Keeping this helper single-sited is
# the DRY constraint from spec-040 Helper-reuse D12 / P1 / P2.
def _validate_mutation_target(mutation_cls: Any) -> None:
    """Reject a bad ``DjangoMutationField`` target at the construction line (spec-036 / spec-038 Decision 5).

    The target must be a **concrete, validated** member of the mutation / form
    family: a class (not an instance / arbitrary value) carrying the mutation
    protocol - a ``_mutation_meta`` attribute and the ``resolve_sync`` /
    ``resolve_async`` + ``input_type_name`` / ``input_module_path`` seams - plus a
    non-``None`` ``_mutation_meta`` (the metaclass stamps it at class creation for a
    concrete subclass; an abstract base carries ``None``).

    The check is **duck-typed**, NOT ``issubclass(DjangoMutation)`` (spec-038
    Decision 5): the plain ``DjangoFormMutation`` is model-less and is NOT a
    ``DjangoMutation`` subclass, and importing the form bases here would close a
    load cycle (``forms/sets.py`` imports ``mutations/sets.py``). So the family is
    recognized by the protocol attrs every flavor carries - the ``036``
    ``DjangoMutation`` (and so ``DjangoModelFormMutation``) and the plain
    ``DjangoFormMutation`` all pass; today's ``DjangoMutation`` behavior is
    unchanged (it carries every protocol attr).

    It does NOT require ``_input_class`` / ``_payload_type_name`` - those are BIND
    outputs populated at ``finalize_django_types``, and the field is constructed at
    import (when ``@strawberry.type class Mutation`` evaluates) BEFORE the bind
    runs. A failure raises ``ConfigurationError`` naming ``DjangoMutationField`` so
    the error fires at the assignment line, not at finalize.
    """
    if not isinstance(mutation_cls, type) or not _has_mutation_protocol(mutation_cls):
        raise ConfigurationError(
            f"DjangoMutationField requires a concrete DjangoMutation / DjangoFormMutation / "
            f"DjangoModelFormMutation subclass; got {mutation_cls!r}.",
        )
    if getattr(mutation_cls, "_mutation_meta", None) is None:
        raise ConfigurationError(
            f"DjangoMutationField requires a concrete mutation subclass with a nested Meta; "
            f"{mutation_cls.__name__} is the abstract base (no Meta).",
        )


def _has_mutation_protocol(mutation_cls: type) -> bool:
    """Return whether a class carries the duck-typed mutation / form-mutation protocol.

    The protocol every dispatchable flavor exposes (the Slice-2 seams): a
    ``_mutation_meta`` attribute (present even as ``None`` on an abstract base, so
    the next guard can distinguish "abstract base" from "not a mutation at all"),
    callable ``resolve_sync`` / ``resolve_async`` (the dispatch seams ``_resolve``
    calls), and callable ``input_type_name`` + an ``input_module_path`` (the
    ``data:`` lazy-ref seams). A class missing any is not a mutation family member.
    """
    if not hasattr(mutation_cls, "_mutation_meta"):
        return False
    return (
        callable(getattr(mutation_cls, "resolve_sync", None))
        and callable(getattr(mutation_cls, "resolve_async", None))
        and callable(getattr(mutation_cls, "input_type_name", None))
        and getattr(mutation_cls, "input_module_path", None) is not None
    )


def _lazy_ref(type_name: str, module_path: str) -> Any:
    """Return ``Annotated[<type_name>, strawberry.lazy(module_path)]``.

    The forward-ref shape ``orders/inputs.py`` uses for its generated classes: a
    string type name resolved through ``<module_path>.__dict__`` at schema build,
    after the phase-2.5 bind materializes the named class as a module global.
    ``module_path`` is a parameter (NOT a hardcoded ``INPUTS_MODULE_PATH``) so the
    ``data:`` ref can name the per-flavor input namespace
    (``mutation_cls.input_module_path``: ``mutations.inputs`` for the model flavor,
    ``forms.inputs`` for the form flavors) while the PAYLOAD-return ref always names
    ``mutations.inputs`` (both flavors materialize their payload there - spec-038
    Decision 5, the load-bearing namespace divergence).
    """
    return Annotated[type_name, strawberry.lazy(module_path)]


def _synthesized_mutation_signature(
    mutation_cls: type,
) -> tuple[inspect.Signature, dict[str, Any]]:
    """Build the per-operation resolver ``__signature__`` + ``__annotations__`` (spec-036 Decision 14 / 7).

    ``root`` / ``info`` are Strawberry-reserved (bound without becoming GraphQL
    args); the operation's GraphQL args follow:

    - ``create``: ``data: <Model>Input!`` (non-null, no default).
    - ``update``: ``id: ID!`` + ``data: <Model>PartialInput!``.
    - ``delete``: ``id: ID!`` only.

    For a form flavor (spec-038): a plain ``DjangoFormMutation`` (the ``"form"``
    operation sentinel) has ``data:`` but NO ``id``; a ``DjangoModelFormMutation``
    create / update follows the model create / update shape. So ``id`` is built for
    ``operation in ("update", "delete")`` and ``data`` for every operation that is
    not ``"delete"`` (create / update / the ``"form"`` sentinel all take ``data:``).

    ``data`` is a ``strawberry.lazy`` forward-ref to the generated input class -
    named via the seams ``mutation_cls.input_type_name(meta)`` +
    ``mutation_cls.input_module_path`` (the model default = ``mutations.inputs`` /
    today's name; the form flavors override to ``forms.inputs`` + the form-input
    name), so the form ``data:`` ref resolves the form-derived input. ``id`` is the
    raw ``strawberry.ID`` string (the ``DjangoNodeField`` server-side-decode
    precedent). The **return** annotation is a ``strawberry.lazy`` forward-ref to
    the generated ``<Name>Payload`` (non-null - the field always returns a payload;
    the object slot inside is nullable). The payload ref ALWAYS names
    ``mutations.inputs`` (``INPUTS_MODULE_PATH``): both flavors materialize their
    payload there, even though the form ``data:`` input lives in ``forms.inputs``
    (the spec-038 Decision 5 namespace divergence - do not conflate them).
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

    if operation != "delete":
        data_ann = _lazy_ref(mutation_cls.input_type_name(meta), mutation_cls.input_module_path)
        params.append(
            inspect.Parameter("data", inspect.Parameter.KEYWORD_ONLY, annotation=data_ann),
        )
        annotations["data"] = data_ann

    return_annotation = _lazy_ref(f"{mutation_cls.__name__}Payload", INPUTS_MODULE_PATH)
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
    # The plain ``DjangoFormMutation`` (the ``"form"`` operation sentinel) has a
    # model-LESS resolver seam whose signature is ``resolve_sync(info, *, data)`` -
    # NO ``id`` param - so passing ``id=`` would be a TypeError. Every model /
    # ``ModelForm`` operation (create / update / delete) DOES take ``id=`` (create
    # passes ``UNSET``, exactly as the ``036`` model dispatch always did), so the
    # only flavor that omits ``id`` is the plain ``"form"`` sentinel (spec-038
    # Slice 3 ``_resolve`` id-kwarg gating).
    takes_id = mutation_cls._mutation_meta.operation != "form"

    def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:  # noqa: ARG001
        data = kwargs.get("data", strawberry.UNSET)
        call_kwargs: dict[str, Any] = {"data": data}
        if takes_id:
            call_kwargs["id"] = kwargs.get("id", strawberry.UNSET)
        if in_async_context():
            return mutation_cls.resolve_async(info, **call_kwargs)
        return mutation_cls.resolve_sync(info, **call_kwargs)

    signature, annotations = _synthesized_mutation_signature(mutation_cls)
    _resolve.__signature__ = signature
    _resolve.__annotations__ = annotations
    return strawberry.field(
        resolver=_resolve,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
