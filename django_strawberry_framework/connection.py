"""``DjangoConnection[T]`` + ``DjangoConnectionField`` - the Relay cursor-pagination surface.

Spec: ``docs/spec-030-connection_field-0_0_9.md``.
Target release: ``0.0.9``.

Slice 1's surface (Decision 3 / Decision 4):

- ``DjangoConnection[NodeType]`` - a generic ``strawberry.relay.ListConnection``
  subclass that owns the package's ``first`` + ``last`` mutual-exclusivity
  guard (which Strawberry's ``SliceMetadata.from_arguments`` does NOT provide)
  and nothing else. It carries no ``total_count`` field.
- ``_connection_type_for(target_type)`` - resolves and caches the connection
  class for a node type: always a generated concrete ``<TypeName>Connection``
  subclass of ``DjangoConnection[target_type]``; the ``totalCount`` opt-in only
  controls whether the ``total_count`` members are added (spec-032 Slice 4 -
  a generic ALIAS handed to the schema loses the ``resolve_connection``
  override at Strawberry's generic specialization, so the bare path must be
  concrete too). The opt-in is read from ``definition.connection`` (the
  ``Meta.connection`` value stored on ``DjangoTypeDefinition``), never
  re-parsed from ``Meta``.

Slice 2's surface (Decision 5 / Decision 6 / Decision 7 / Decision 10):

- ``DjangoConnectionField(target_type, *, resolver=None, ...)`` - the PascalCase
  factory: validates the target (the four ``DjangoListField``-style guards plus
  a Relay-Node guard), synthesizes a resolver whose ``__signature__`` carries
  the ``filter`` / ``order_by`` parameters derived from the type's sidecars
  (so Strawberry's native resolver-argument derivation emits ``filter:`` /
  ``orderBy:``), and returns ``relay.connection(_connection_type_for(target_type),
  resolver=<synthesized>, ...)``.
- The synthesized resolver runs the composition pipeline
  (visibility -> filter -> orderBy -> default-order -> optimizer-plan) before
  ``ConnectionExtension`` slices the queryset, with the ``Manager`` / ``QuerySet``
  / non-queryset-iterable consumer-``resolver=`` contract.

The public exports (``DjangoConnection`` / ``DjangoConnectionField``) land in
Slice 4 alongside the live fakeshop usage; until then the symbols are referenced
by their module path.
"""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable, Iterable, Sequence
from typing import Any, Generic, TypeVar

import strawberry
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from graphql import GraphQLError
from strawberry import relay
from strawberry.relay.types import NodeIterableType
from strawberry.types import Info
from strawberry.types.nodes import FragmentSpread, InlineFragment, Selection
from strawberry.utils.await_maybe import AwaitableOrValue

from .exceptions import ConfigurationError
from .list_field import _is_async_callable, _validate_djangotype_target
from .optimizer.extension import apply_connection_optimization
from .types.base import _is_relay_shaped
from .types.relay import (
    _apply_get_queryset_async,
    _apply_get_queryset_sync,
    _initial_queryset,
)

NodeType = TypeVar("NodeType")

# Field name carried on the connection instance for the captured ``totalCount``;
# ``None`` (the default) means the count was not requested / not run, which the
# ``total_count`` field resolver returns verbatim per the selection-gating
# contract (Decision 4).
_TOTAL_COUNT_ATTR = "_django_total_count"


def _guard_first_and_last(first: int | None, last: int | None) -> None:
    """Raise ``GraphQLError`` when both ``first`` and ``last`` are supplied.

    The package's own pagination guard (Decision 3): Strawberry's
    ``SliceMetadata.from_arguments`` applies ``first`` then ``last`` without a
    mutual-exclusivity check, so the package enforces it here - a query-runtime
    error landing in the GraphQL ``errors`` array, NOT a construction-time
    ``ConfigurationError``. Single-sited so the literal lives once and both the
    base and the generated ``<TypeName>Connection`` reuse it.
    """
    if first is not None and last is not None:
        raise GraphQLError(
            "Connection arguments `first` and `last` are mutually exclusive; supply only one.",
        )


def _total_count_requested(info: Info) -> bool:
    """Return whether the query selects the connection's ``totalCount`` field.

    Checks the connection field's DIRECT children (``totalCount`` is a sibling
    of ``edges`` / ``pageInfo``); the GraphQL field name is camelCase
    ``totalCount`` regardless of the Python ``total_count`` attribute.

    Scoped to the direct children deliberately (``docs/feedback.md`` P2): unlike
    strawberry-django's ``_should_optimize_total_count``, which recurses through
    the WHOLE ``edges { node { ... } }`` subtree, ``_check`` recurses only THROUGH
    fragment wrappers (``InlineFragment`` / ``FragmentSpread`` - so a
    fragment-wrapped ``totalCount`` at the connection level still counts) and
    does NOT descend into a regular field's selections. Once nested connections
    land (WIP-032/033), a node-level ``totalCount`` deep inside ``edges { node
    { ... } }`` must not make the OUTER connection's predicate fire (a spurious
    ``COUNT`` and, on a non-queryset source, a spurious M1-guard raise).
    """

    def _check(selection: Selection) -> bool:
        if isinstance(selection, (InlineFragment, FragmentSpread)):
            # Recurse THROUGH fragment wrappers, not into regular fields.
            # (``InlineFragment`` has no ``.name`` - check the type first.)
            return any(_check(child) for child in selection.selections)
        return selection.name == "totalCount"

    return any(
        _check(selection)
        for selected_field in info.selected_fields
        for selection in selected_field.selections
    )


class DjangoConnection(relay.ListConnection[NodeType], Generic[NodeType]):
    """Generic Relay connection base owning the ``first`` + ``last`` guard.

    Subclasses ``strawberry.relay.ListConnection`` so Strawberry owns cursor
    encoding, ``pageInfo``, edge wrapping, and the slice window. The only
    behavior this base adds is the Decision 3 ``first`` + ``last`` guard in the
    ``resolve_connection`` override; it carries no ``total_count`` field (that
    is the opt-in ``<TypeName>Connection`` variant's job, Decision 4).
    """

    @classmethod
    def resolve_connection(
        cls,
        nodes: NodeIterableType[NodeType],
        *,
        info: Info,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        max_results: int | None = None,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        """Apply the ``first`` + ``last`` guard, then delegate to ``ListConnection``."""
        _guard_first_and_last(first, last)
        return super().resolve_connection(
            nodes,
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=max_results,
            **kwargs,
        )


_connection_type_cache: dict[type, type] = {}


def clear_connection_type_cache() -> None:
    """Clear the per-target generated-connection-class cache.

    Test-only - production never reloads the schema. Wired into
    ``registry.clear()`` (the documented registry reset) so a registry-clearing
    test or fixture also drops the generated ``<TypeName>Connection`` classes,
    rather than accumulating dead identity-keyed entries across schema reloads
    (``docs/feedback.md`` P3b). The cache is keyed on ``target_type`` identity,
    so a stale entry is never *wrong* - this clear is hygiene, not correctness.
    """
    _connection_type_cache.clear()


def _generate_connection_class(
    target_type: type,
    populate: Callable[[dict], None] | None = None,
    *,
    description: str | None = None,
) -> type:
    """Generate a concrete ``<TypeName>Connection`` subclass of ``DjangoConnection[target_type]``.

    The single-sited generation tail shared by both ``_connection_type_for``
    branches: ``populate`` (when given) fills the class namespace (the
    ``totalCount`` variant's members); ``description`` is forwarded to
    ``strawberry.type`` (the bare variant preserves the parent's inherited SDL
    description; the opted variant ships description-less, today's SDL shape).

    Name the generated connection from the node type's canonical GraphQL type
    name (``graphql_type_name`` - ``Meta.name`` when set, else the Python
    ``__name__``), NOT the raw Python ``__name__``. Two DjangoType classes may
    share a Python ``__name__`` while declaring distinct ``Meta.name`` values;
    naming from ``__name__`` would generate two connection classes with the
    SAME SDL type name, which Strawberry collapses into one - cross-wiring the
    two fields' ``edges`` / node types (P1, ``docs/feedback.md``).
    ``graphql_type_name`` is the same surface-name source the finalizer and the
    filter / order input types derive from.
    """
    definition = target_type.__django_strawberry_definition__
    generated = types.new_class(
        f"{definition.graphql_type_name}Connection",
        (DjangoConnection[target_type],),
        exec_body=populate,
    )
    return strawberry.type(generated, description=description)


def _build_total_count_connection(target_type: type) -> type:
    """Generate the concrete ``<TypeName>Connection`` carrying ``totalCount``.

    The generated class subclasses ``DjangoConnection[target_type]`` (so it
    inherits the ``first`` + ``last`` guard), declares a ``total_count`` field
    whose resolver reads a private instance attribute, and overrides
    ``resolve_connection`` to count the post-filter pre-slice ``nodes``
    queryset (sync ``.count()`` / async ``.acount()``) ONLY when ``totalCount``
    is in the selection set, attach the count to the connection instance, then
    delegate to super for slicing (Decision 4).
    """

    @strawberry.field(description="Total number of nodes in the connection.")
    def total_count(self: Any) -> int:
        # The field renders ``Int!`` (the ``__annotations__`` below win for the
        # SDL); ``-> int`` is the honest return type because the count path is
        # QuerySet-only (the connection field's M1 rule raises a ``GraphQLError``
        # before a non-queryset return can reach ``totalCount``). The attribute
        # is always set by ``resolve_connection`` when the field is selected
        # over a queryset source.
        return getattr(self, _TOTAL_COUNT_ATTR)

    @classmethod
    def resolve_connection(
        cls: type,
        nodes: NodeIterableType[NodeType],
        *,
        info: Info,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        max_results: int | None = None,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        # Delegate to super FIRST. The inherited ``DjangoConnection.resolve_connection``
        # runs the ``first`` + ``last`` guard before slicing (L1: the explicit
        # call here was a redundant double-run; the guard literal stays
        # single-sited in ``_guard_first_and_last``, and running super first
        # preserves the guard-before-anything-else ordering). ``want_count`` is
        # computed only after the guard has passed.
        conn = super(generated, cls).resolve_connection(
            nodes,
            info=info,
            before=before,
            after=after,
            first=first,
            last=last,
            max_results=max_results,
            **kwargs,
        )
        want_count = _total_count_requested(info)
        if inspect.isawaitable(conn):
            return _attach_count_async(conn, nodes, want_count=want_count)
        return _attach_count_sync(conn, nodes, want_count=want_count)

    def _populate(namespace: dict) -> None:
        namespace["__annotations__"] = {"total_count": int}
        namespace["total_count"] = total_count
        namespace["resolve_connection"] = resolve_connection

    # ``description=None`` keeps the opted variant's shipped description-less
    # SDL shape (the bare/opted description asymmetry is shipped surface - see
    # ``_connection_type_for``).
    generated = _generate_connection_class(target_type, _populate, description=None)
    return generated


def _guard_total_count_countable(nodes: Any, *, want_count: bool) -> None:
    """Raise ``GraphQLError`` when ``totalCount`` is selected over a non-queryset.

    The M1 carry-forward (Decision 7): ``totalCount`` renders ``Int!``, and a
    non-queryset iterable cannot be ``.count()``-ed. Rather than skip the count
    and let the ``Int!`` field return ``None`` (which surfaces as the engine's
    opaque ``Cannot return null for non-nullable field ...totalCount`` violation),
    raise a clear package error - symmetric with the sidecar-input rule in
    ``_post_process_consumer_*``. Single-sited so the sync and async count
    helpers share one rule.
    """
    if want_count and not isinstance(nodes, models.QuerySet):
        raise GraphQLError(
            "`totalCount` was selected on a connection whose resolver returned a "
            "non-queryset iterable; `totalCount` requires a QuerySet source it "
            "can count. Return a QuerySet (or a Manager) from the connection "
            "resolver, or do not select `totalCount`.",
        )


def _attach_count_sync(conn: Any, nodes: Any, *, want_count: bool) -> Any:
    """Attach the post-filter pre-slice count to a resolved connection (sync)."""
    _guard_total_count_countable(nodes, want_count=want_count)
    if want_count:
        setattr(conn, _TOTAL_COUNT_ATTR, nodes.count())
    return conn


async def _attach_count_async(conn_awaitable: Any, nodes: Any, *, want_count: bool) -> Any:
    """Attach the post-filter pre-slice count to a resolved connection (async)."""
    # Await-before-raise (mirrors the close-before-raise discipline in
    # ``types/relay.py::_apply_get_queryset_sync``, Decision 10): resolve the
    # queued connection coroutine BEFORE the guard can raise, so a guard-raise
    # never leaves ``conn_awaitable`` unawaited (which would emit a
    # ``RuntimeWarning`` - a hard failure under ``-W error``). The guard's
    # decision depends only on ``nodes`` / ``want_count``, never on ``conn``,
    # so awaiting first is side-effect-safe.
    conn = await conn_awaitable
    _guard_total_count_countable(nodes, want_count=want_count)
    if want_count:
        setattr(conn, _TOTAL_COUNT_ATTR, await nodes.acount())
    return conn


def _connection_type_for(target_type: type) -> type:
    """Return (and cache) the connection class for a node ``DjangoType``.

    Always returns a generated concrete ``<TypeName>Connection`` subclass of
    ``DjangoConnection[target_type]``. ``target_type``'s ``definition.connection``
    slot (the validated ``Meta.connection`` value) only controls the shape:
    opting into ``total_count`` adds the ``totalCount`` members; otherwise the
    subclass adds nothing over the base. Cached on ``target_type`` identity -
    one connection shape per node type, no per-field override (Decision 5), so
    the generated name is unique and regeneration is avoided.
    """
    cached = _connection_type_cache.get(target_type)
    if cached is not None:
        return cached

    definition = target_type.__django_strawberry_definition__
    connection_options = definition.connection
    if connection_options and connection_options.get("total_count"):
        connection_type: type = _build_total_count_connection(target_type)
    else:
        # WHY concrete and not the ``DjangoConnection[target_type]`` alias:
        # handing the schema a generic ALIAS loses the package's
        # ``resolve_connection`` override - Strawberry's schema-build generic
        # specialization copies the alias into a plain specialized class whose
        # ``resolve_connection`` is ``ListConnection``'s, so the ``first`` +
        # ``last`` guard never ran through-schema (the spec-032 Slice-4
        # discovered bug). A concrete class is used as-is by the schema build,
        # so the override survives. The description is read from the parent's
        # strawberry definition (never copied as a package literal), preserving
        # the previous bare-alias SDL byte-for-byte.
        connection_type = _generate_connection_class(
            target_type,
            description=DjangoConnection.__strawberry_definition__.description,
        )
    _connection_type_cache[target_type] = connection_type
    return connection_type


# =============================================================================
# DjangoConnectionField - factory, synthesized-signature resolver, pipeline
# =============================================================================


def _guard_sidecar_input_against_non_queryset(source: Any, *, has_sidecar_input: bool) -> None:
    """Raise ``GraphQLError`` when ``filter:`` / ``orderBy:`` is supplied over a non-queryset.

    The consumer-``resolver=`` contract (Decision 7): a non-queryset iterable
    (list / generator) may be paginated only when NO ``filter:`` / ``orderBy:``
    input is supplied. The advertised Meta-driven filter/order behavior is a
    queryset operation and cannot apply to a plain iterable, so supplying
    sidecar input against one is a clear package error rather than a silently
    ignored argument. Symmetric with the ``totalCount`` rule in
    ``_guard_total_count_countable``.
    """
    if has_sidecar_input and not isinstance(source, models.QuerySet):
        raise GraphQLError(
            "`filter:` / `orderBy:` was supplied to a connection whose resolver "
            "returned a non-queryset iterable; these arguments narrow a QuerySet "
            "and cannot apply to a plain iterable. Return a QuerySet (or a "
            "Manager) from the connection resolver, or omit `filter:` / `orderBy:`.",
        )


def _ends_in_unique_column(effective: tuple, model: type) -> bool:
    """Return whether the effective ordering's terminal entry is a unique total-order column.

    A connection's positional offset cursors are only stable across separate
    requests when the SQL ``ORDER BY`` is a deterministic TOTAL order. An
    ordering whose terminal column is unique (the pk, or a ``unique=True`` model
    field) already is one; otherwise ``_finalize_queryset`` appends the pk as a
    terminal tiebreaker (``docs/feedback.md`` P1).

    Handles both string order refs (``"name"``, ``"-name"``, ``"shelf__code"``,
    ``"pk"``) and ``OrderBy`` / ``F`` expressions (the NULLS-positioning and the
    to-many-aggregate paths). A relation path, an aggregate-annotation alias, or
    any non-``F`` expression is treated as non-unique (so the pk is appended).
    """
    if not effective:
        return False
    terminal = effective[-1]
    if isinstance(terminal, str):
        ref: str | None = terminal.lstrip("-")
    else:
        ref = getattr(getattr(terminal, "expression", None), "name", None)
    if not ref:
        return False
    pk = model._meta.pk
    if ref in ("pk", pk.name, pk.attname):
        return True
    if "__" in ref:
        # A relation traversal (e.g. ``shelf__code``) is not the model's own
        # unique column; the related column's uniqueness does not make the
        # parent ordering a total order.
        return False
    try:
        field = model._meta.get_field(ref)
    except FieldDoesNotExist:
        # Annotation alias (e.g. a to-many aggregate) or a transform - not a
        # model column we can call unique.
        return False
    return bool(getattr(field, "unique", False) or getattr(field, "primary_key", False))


def _finalize_queryset(target_type: type, qs: models.QuerySet, info: Info) -> models.QuerySet:
    """Apply the color-agnostic pipeline tail: deterministic total order, then optimizer plan.

    Steps 5-6 of the Decision 7 pipeline. Single-sited so the sync and async
    resolver bodies share one implementation of the steps that do no I/O (the
    default ``order_by`` and the optimizer plan are pure queryset-method calls
    on a lazy queryset):

    5. Deterministic TOTAL ordering - the connection's positional offset cursors
       (Strawberry's ``ListConnection``) are only stable across separate
       requests when the ``ORDER BY`` is a unique total order. So append the pk
       as a terminal tiebreaker UNLESS the effective ordering already ends in a
       unique column (``_ends_in_unique_column``). This covers all three cases -
       fully unordered, a supplied ``orderBy``, and a model ``Meta.ordering`` -
       not just the unordered one (``docs/feedback.md`` P1).

       The effective ordering must NOT be read from ``qs.query.order_by`` alone:
       that tuple is EMPTY when the order comes from model ``Meta.ordering``
       (Django applies ``_meta.ordering`` implicitly) even though ``qs.ordered``
       is True, so reading it in isolation would drop ``Meta.ordering`` and
       rewrite ``ORDER BY name`` into ``ORDER BY pk``. Fall back to
       ``_meta.ordering`` when ``qs.query.order_by`` is empty.
    6. Optimizer plan - ``apply_connection_optimization`` applies
       ``select_related`` / ``prefetch_related`` / ``only()`` using the node
       type / model explicitly (the connection field's own cooperation point,
       Decision 11), because the schema middleware never sees the pre-slice
       queryset behind ``ConnectionExtension``.
    """
    target_model = target_type.__django_strawberry_definition__.model
    effective = tuple(qs.query.order_by) or tuple(target_model._meta.ordering)
    if not _ends_in_unique_column(effective, target_model):
        qs = qs.order_by(*effective, target_model._meta.pk.attname)
    return apply_connection_optimization(target_type, qs, info)


def _pipeline_sync(
    target_type: type,
    source: Any,
    info: Info,
    *,
    filter_input: Any,
    order_by_input: Any,
) -> Any:
    """Run the composition pipeline on the sync path (Decision 7 / Decision 10).

    ``source`` is the base value (the consumer ``resolver=`` return or the
    default ``_initial_queryset``). A ``Manager`` is coerced to a ``QuerySet``;
    a ``QuerySet`` receives steps 2-6 (visibility -> filter -> orderBy ->
    default-order -> optimizer); a non-queryset iterable is passed through
    unchanged after the sidecar-input guard rejects ``filter:`` / ``orderBy:``.
    """
    definition = target_type.__django_strawberry_definition__
    if isinstance(source, models.Manager):
        source = source.all()
    has_sidecar_input = filter_input is not None or order_by_input is not None
    if not isinstance(source, models.QuerySet):
        _guard_sidecar_input_against_non_queryset(source, has_sidecar_input=has_sidecar_input)
        return source
    qs = _apply_get_queryset_sync(target_type, source, info)
    if filter_input is not None and definition.filterset_class is not None:
        qs = definition.filterset_class.apply_sync(filter_input, qs, info)
    if order_by_input is not None and definition.orderset_class is not None:
        qs = definition.orderset_class.apply_sync(order_by_input, qs, info)
    return _finalize_queryset(target_type, qs, info)


async def _pipeline_async(
    target_type: type,
    source: Any,
    info: Info,
    *,
    filter_input: Any,
    order_by_input: Any,
) -> Any:
    """Async sibling of ``_pipeline_sync`` - awaits the colored visibility / filter / order steps."""
    definition = target_type.__django_strawberry_definition__
    if isinstance(source, models.Manager):
        source = source.all()
    has_sidecar_input = filter_input is not None or order_by_input is not None
    if not isinstance(source, models.QuerySet):
        _guard_sidecar_input_against_non_queryset(source, has_sidecar_input=has_sidecar_input)
        return source
    qs = await _apply_get_queryset_async(target_type, source, info)
    if filter_input is not None and definition.filterset_class is not None:
        qs = await definition.filterset_class.apply_async(filter_input, qs, info)
    if order_by_input is not None and definition.orderset_class is not None:
        qs = await definition.orderset_class.apply_async(order_by_input, qs, info)
    return _finalize_queryset(target_type, qs, info)


def _synthesized_signature(target_type: type) -> tuple[inspect.Signature, dict[str, Any]]:
    """Build the resolver ``__signature__`` + ``__annotations__`` carrying the sidecar args.

    Decision 6: the resolver's signature is the SDL contract. The return
    annotation is ``Iterable[target_type]`` (which ``ConnectionExtension.apply``
    requires); ``info`` is included so the resolver receives it; ``filter`` /
    ``order_by`` are added only for the sidecars the type declares, with the
    SAME ``filter_input_type(FS)`` / ``list[order_input_type(OS)]`` lazy
    ``Annotated`` shapes a hand-written filter/order resolver uses. Calling
    those helpers ALSO registers the FilterSet / OrderSet against the
    ``_helper_referenced_filtersets`` / ``_helper_referenced_ordersets`` orphan
    ledgers, so ``finalize_django_types`` orphan validation stays honest - no
    separate ``.add(...)`` is needed or wanted. The ``search:`` argument is NOT
    generated (search is ``0.1.2``).
    """
    # Imported at call time (schema build), not module scope: a module-level
    # import would make bare ``import django_strawberry_framework`` (which pulls
    # in ``connection`` via ``__init__``) eagerly import the ``filters`` /
    # ``orders`` subpackages, breaking the lazy-subpackage contract pinned by
    # ``tests/filters/test_finalizer.py`` and ``tests/orders/test_inputs.py``.
    # These helpers are only needed when building a field's synthesized
    # signature, so a function-local import keeps the top-level package import
    # lazy while preserving the generated ``filter:`` / ``orderBy:`` arguments.
    from .filters import filter_input_type
    from .orders import order_input_type

    definition = target_type.__django_strawberry_definition__
    # ``root`` and ``info`` are Strawberry reserved parameter names: the engine
    # binds the source value to ``root`` and the resolver ``Info`` to ``info``
    # WITHOUT exposing either as a GraphQL argument. Declaring them in the
    # synthesized signature means Strawberry passes both at call time (so the
    # consumer-``resolver=`` path gets ``root`` / ``info``) while only the
    # sidecar params below become real arguments.
    params: list[inspect.Parameter] = [
        inspect.Parameter("root", inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None),
        inspect.Parameter("info", inspect.Parameter.KEYWORD_ONLY, annotation=Info),
    ]
    annotations: dict[str, Any] = {"info": Info}
    if definition.filterset_class is not None:
        filter_ann = filter_input_type(definition.filterset_class) | None
        params.append(
            inspect.Parameter(
                "filter",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=filter_ann,
            ),
        )
        annotations["filter"] = filter_ann
    if definition.orderset_class is not None:
        order_ann = list[order_input_type(definition.orderset_class)] | None
        params.append(
            inspect.Parameter(
                "order_by",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=order_ann,
            ),
        )
        annotations["order_by"] = order_ann
    return_annotation = Iterable[target_type]
    annotations["return"] = return_annotation
    return inspect.Signature(params, return_annotation=return_annotation), annotations


def _build_connection_resolver(target_type: type, resolver: Callable | None) -> Callable:
    """Build the field resolver: the pipeline body plus the synthesized signature.

    The body pops ``filter`` / ``order_by`` (forwarded by ``ConnectionExtension``
    as ``**kwargs``) and runs the composition pipeline. Sync-vs-async dispatch is
    committed per-construction (Decision 10), because Strawberry freezes a
    field's resolver sync/async handling at schema-build time AND, unlike a plain
    field, ``ConnectionExtension`` only awaits an awaitable inner-resolver return
    when the field is async (``ConnectionExtension.resolve`` - the sync path -
    passes the resolver return straight to ``resolve_connection`` without
    awaiting; only ``resolve_async`` awaits). So a per-call coroutine return from
    a sync resolver (the ``DjangoListField`` shape) would NOT be awaited here:

    - **Default branch** (``resolver is None``) and the **sync consumer-resolver**
      branch are sync resolvers running ``_pipeline_sync``, which returns a LAZY
      queryset. A lazy queryset works under BOTH ``execute_sync`` and
      ``await execute`` - ``resolve_connection`` / ``ListConnection`` materialize
      it with ``.count()`` (sync) or ``.acount()`` (async) per the runtime
      context, so async counting still happens for the default field. A sync
      pipeline meeting an async ``get_queryset`` raises ``SyncMisuseError`` (the
      Relay-foundation contract); to drive an async ``get_queryset`` hook through
      a connection, supply an ``async def`` ``resolver=`` (below).
    - **Async consumer-resolver** branch (``_is_async_callable(resolver)``) is an
      ``async def`` resolver running ``_pipeline_async`` - being ``async def``
      makes the field async, so ``ConnectionExtension.resolve_async`` awaits its
      return and the async ``get_queryset`` / ``apply_async`` hooks run on the
      async path.
    """
    if resolver is None:

        def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:  # noqa: ARG001
            return _pipeline_sync(
                target_type,
                _initial_queryset(target_type),
                info,
                filter_input=kwargs.get("filter"),
                order_by_input=kwargs.get("order_by"),
            )

    elif _is_async_callable(resolver):

        async def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:
            source = await resolver(root, info)
            return await _pipeline_async(
                target_type,
                source,
                info,
                filter_input=kwargs.get("filter"),
                order_by_input=kwargs.get("order_by"),
            )

    else:

        def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:
            return _pipeline_sync(
                target_type,
                resolver(root, info),
                info,
                filter_input=kwargs.get("filter"),
                order_by_input=kwargs.get("order_by"),
            )

    signature, annotations = _synthesized_signature(target_type)
    _resolve.__signature__ = signature
    _resolve.__annotations__ = annotations
    return _resolve


def _build_relation_connection_resolver(target_type: type, accessor_name: str) -> Callable:
    """Build the resolver for a Phase-2.5 synthesized relation connection (spec-032 Decision 6).

    Identical pipeline tail to ``_build_connection_resolver``'s default branch,
    but the source queryset seeds from the PARENT'S relation manager
    (``getattr(root, accessor_name).all()``) - keeping Django's prefetch caches
    reachable as the cooperation seam ``WIP-ALPHA-033-0.0.9``'s
    window-pagination planning will use - instead of
    ``model._default_manager.all()``. ``accessor_name`` is the same
    ``field.name`` the shipped many-side list resolver reads
    (``types/resolvers.py::many_resolver``), so the list field and its
    connection sibling can never disagree about which manager they traverse.

    Sync resolver returning a LAZY queryset by design (the
    committed-at-construction contract on ``_build_connection_resolver`` holds
    verbatim: a lazy queryset works under both ``execute_sync`` and
    ``await execute``). Deliberately ABSENT: any ``DST_OPTIMIZER_STRICTNESS``
    / ``DST_OPTIMIZER_PLANNED`` consultation - the connection pipeline stays
    strictness-blind and derives an empty optimizer plan until ``033`` wires
    it (spec-032 Decision 12 / Non-goals).

    Async-``get_queryset`` posture (0.0.9): this is sync-pipeline-only and has
    no ``resolver=`` seam (the documented escape a *root* connection uses for
    an async hook), so a Relay target whose ``get_queryset`` is ``async def``
    raises ``SyncMisuseError`` on every query of its synthesized
    ``<field>Connection``; ``relation_shapes = {"<field>": "list"}`` is the
    recourse until an async connection pipeline rides the ``033`` work. The
    fail-loud ``SyncMisuseError`` is inherited from the pipeline, not new here.
    """

    def _resolve(root: Any, info: Info, **kwargs: Any) -> Any:
        return _pipeline_sync(
            target_type,
            getattr(root, accessor_name).all(),
            info,
            filter_input=kwargs.get("filter"),
            order_by_input=kwargs.get("order_by"),
        )

    signature, annotations = _synthesized_signature(target_type)
    _resolve.__signature__ = signature
    _resolve.__annotations__ = annotations
    return _resolve


def DjangoConnectionField(  # noqa: N802  # PascalCase for graphene-django parity - consumer usage is `DjangoConnectionField(GenreType)`
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
) -> Any:
    """Factory for a Relay connection field over a Relay-Node-shaped ``DjangoType``.

    Meta-only derivation (Decision 5): the ``filter:`` / ``orderBy:`` arguments
    come from the type's ``Meta.filterset_class`` / ``Meta.orderset_class``, the
    ``totalCount`` opt-in from ``Meta.connection`` - there are no ``filters=`` /
    ``order=`` / ``total_count=`` keyword arguments. Runs the four
    ``DjangoListField``-style guards plus a Relay-Node guard, then returns
    ``relay.connection(_connection_type_for(target_type), resolver=<synthesized>,
    ...)`` (Decision 6 / Decision 7).

    Consumer ``resolver=`` contract: the resolver is invoked as
    ``resolver(root, info)`` and returns only the BASE queryset / manager /
    iterable. It never receives the ``filter:`` / ``orderBy:`` arguments - the
    synthesized resolver consumes those and the pipeline applies them to the
    resolver's return (the same shape as ``DjangoListField``). A resolver that
    declares its own ``filter`` / ``order_by`` parameters will not be handed
    them; use ``Meta.filterset_class`` / ``Meta.orderset_class`` to shape the
    sidecar arguments.
    """
    # The four shared ``DjangoType``-target guards (see
    # ``list_field.py::_validate_djangotype_target`` for the load-bearing
    # ordering and the own-class ``definition.origin is target_type`` invariant).
    _validate_djangotype_target(target_type, resolver, field="DjangoConnectionField")
    # Re-derive ``definition`` for the connection-specific Relay-Node guard
    # below (and the downstream ``_connection_type_for`` path). The shared
    # helper does its own internal lookup for guard 3 and returns ``None``.
    definition = getattr(target_type, "__django_strawberry_definition__", None)
    # The fifth, connection-specific guard: a connection is only meaningful over
    # a Relay-Node-shaped type. Reuse the canonical ``_is_relay_shaped(cls,
    # interfaces)`` predicate (the single source of truth in ``types/base.py``),
    # which accepts EITHER spelling at construction time:
    #   * ``relay.Node`` in the declared ``Meta.interfaces`` tuple - the
    #     Meta-driven spelling. The tuple is populated at class creation, before
    #     ``finalize_django_types()`` (Phase 2.5 ``apply_interfaces``) injects
    #     ``relay.Node`` into ``__bases__``, so a plain MRO check
    #     (``implements_relay_node``) would wrongly reject it at this call site.
    #   * direct inheritance (``class Foo(DjangoType, relay.Node)``) - ``relay.Node``
    #     is in ``__bases__`` from class definition, so ``issubclass(target_type,
    #     relay.Node)`` is already True here. The finalizer fully supports this
    #     Strawberry-native spelling (it keys Relay finalization off
    #     ``implements_relay_node``, not a non-empty ``Meta.interfaces``), so the
    #     connection field accepts it too (``docs/feedback.md`` Open Question).
    if not _is_relay_shaped(target_type, definition.interfaces):
        raise ConfigurationError(
            "a connection field requires a Relay-Node-shaped DjangoType; add "
            "`relay.Node` to `Meta.interfaces` (or inherit `relay.Node` directly)",
        )
    return relay.connection(
        _connection_type_for(target_type),
        resolver=_build_connection_resolver(target_type, resolver),
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
