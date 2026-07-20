"""Shared query-source, field-coercion, sync/async hook, and visibility contracts.

The neutral query-source mechanics every resolver surface shares: coerce a
``Manager`` to a ``QuerySet`` exactly once, decide whether a value is a
queryset, run the ``DjangoType.get_queryset`` visibility hook through the sync
or async path, and combine those into the list-field consumer-resolver shape.
Extracted here (the 0.0.9 DRY pass, ``docs/feedback.md`` Major 1) so list
fields, connection fields, the optimizer middleware, the Relay node defaults,
and the filter related-visibility derive all reach ONE implementation of the
contract -- ``get_queryset`` is the visibility hook, and a visibility-hook
mistake is a data-leak bug, so the routing must not be re-decided per surface.

``coerce_field_value_or_none`` (0.0.13 DRY pass) is the sibling neutral
primitive for the "raw literal -> Django field value, or nothing" safety
wrapper the Relay id decode, the raw relation-pk decode, and the ``__in``
filter member decode each need against a DIFFERENT field - single-sourcing the
coercion mechanics while leaving the field selection to each caller.

``run_in_one_sync_boundary`` (0.0.13 DRY pass) is the sibling neutral
primitive for "run a sync callable in exactly one
``sync_to_async(thread_sensitive=True)`` worker" - shared by filters /
orders / cascade permissions / mutation-form pipelines / session auth so
the off-event-loop boundary cannot drift.

The two colored visibility runners are the package's hardened ``get_queryset``
security boundary (the get_queryset-visibility-boundary decision): every
framework-owned invocation of the hook routes through them, so source
preparation and result normalization live in exactly one place rather than per
surface.

The boundary implements a SEALED-EXECUTION-QUERYSET contract
(``_seal_or_defect``). An earlier design validated a finite inventory of method
overrides on the consumer ``QuerySet`` *class* and then returned the consumer
object; an adversarial review (``docs/feedback.md``) disproved that with
zero-SQL probes -- an instance-shadowed ``.all()``, a replaced instance-level
``Query.chain``, and subclass ``.filter()`` / ``_values`` / ``.first()`` /
``.__aiter__()`` overrides each erased the visibility predicate or returned
synthetic rows AFTER a class-level inventory accepted the object. A finite
inventory is the wrong abstraction. Instead the boundary treats the consumer
queryset as untrusted query STATE: it reads that state without dispatching any
consumer code (every read comes from the instance ``__dict__`` via
``object.__getattribute__``, so a custom ``__getattribute__`` or an
instance-shadowed attribute cannot lie or run code), validates it, then rebuilds
a framework-owned plain ``django.db.models.QuerySet`` from the validated state.
It NEVER returns the consumer object.

What the seal preserves: the SQL query state (filters, annotations, joins,
ordering, combinators, values projection), database routing / hints, and the
prefetch metadata Django needs -- everything that determines which rows the SQL
selects. What it deliberately drops: the consumer's executable override dispatch
(the subclass identity itself), because that is precisely the leak vector. A
foreign ``Query`` class, a foreign row-iterable class, or an unresolved deferred
filter cannot be faithfully rebuilt, so they fail closed (``untrusted``).

Caller-specific tails stay with their caller: the connection field keeps its
GraphQL non-queryset error (it calls ``normalize_query_source`` then guards),
the Relay node defaults keep their id filter, the optimizer keeps plan
building, and the filter related derive keeps its per-branch recursion. This
module owns only the source normalization + the colored visibility calls.

Cycle-safe by construction: it depends on ``django``, ``asgiref``,
``..exceptions``, and the write-transaction ContextVar helpers, so
``types/relay.py`` (imported at module top by ``types/base.py``) can import
from here without closing a load cycle, and it never imports back into
filters / orders / mutations / permissions.
"""

from __future__ import annotations

import asyncio
import datetime
import inspect
import sys
import uuid
from decimal import Decimal
from typing import Any

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch, sql
from django.db.models.query import (
    PROHIBITED_FILTER_KWARGS,
    FlatValuesListIterable,
    ModelIterable,
    NamedValuesListIterable,
    ValuesIterable,
    ValuesListIterable,
)
from django.db.models.sql.where import WhereNode

from ..exceptions import ConfigurationError
from .write_transaction import base_locked_queryset, current_write_pipeline, pin_write_queryset


class SyncMisuseError(ConfigurationError, RuntimeError):
    """Raised when a sync resolver context encounters an async ``get_queryset``.

    Typed marker for the "async ``get_queryset`` hook invoked from a
    sync resolver" misuse. Multiple-inherits ``ConfigurationError``
    AND ``RuntimeError`` so callers catching either base class still
    match:

    - ``except ConfigurationError`` (the package's convention for
      configuration-time errors).
    - ``except RuntimeError`` (consumer code catching ``RuntimeError``
      after the ``FilterSet.apply`` dispatcher rethrow continues to
      work).

    The dispatcher in ``filters/sets.py::FilterSet.apply`` catches
    this subclass directly. Consumers who want a focused catch should
    also match the subclass. Exported through
    ``django_strawberry_framework`` (and re-exported from
    ``django_strawberry_framework.types.relay`` for back-compat) so it
    can be imported without reaching into this private ``utils`` module.
    """


def reject_async_in_sync_context(
    value: Any,
    *,
    owner: str,
    method: str,
    context: str,
    recourse: str,
) -> Any:
    """Guard a synchronous hook result against any awaitable return.

    Three sync pipeline seams invoke a consumer-overridable hook that
    Decision 9 / Decision 15 allow to be sync OR async: the ``get_queryset``
    visibility hook (``apply_type_visibility_sync``) and the two write
    authorization hooks (``check_permission`` / a ``permission_classes``
    entry's ``has_permission``). None can await - the whole ORM pipeline runs
    synchronously (under one ``sync_to_async`` worker on the async surface),
    so an ``async def`` override returns an orphaned coroutine. Treating that
    truthy coroutine as success would be a silent bug - an authorization
    BYPASS for the permission hooks - so it is rejected loudly.

    Awaitables cannot be consumed by these sync pipelines. Native coroutines
    are closed and futures are cancelled before ``SyncMisuseError`` is raised;
    other awaitables have no standard cleanup protocol. Native-coroutine error
    text is preserved for compatibility. Otherwise ``value`` is returned
    unchanged, so callers read ``x = reject_async_in_sync_context(x, ...)``.
    """
    if inspect.isawaitable(value):
        kind = "a coroutine" if inspect.iscoroutine(value) else "an awaitable"
        _dispose_sync_awaitable(value)
        raise SyncMisuseError(
            f"{owner}.{method} returned {kind} in a sync {context} context. {recourse}",
        )
    return value


def _dispose_sync_awaitable(value: Any) -> None:
    """Release a rejected awaitable without awaiting it, when possible.

    Native coroutines are closed and futures cancelled; other awaitables have
    no standard cleanup protocol. Used by every boundary that refuses an
    awaitable - the sync misuse guards AND the async runners' nested /
    residual awaitable rejections (those must not recursively await an
    unbounded chain, so disposal is the only safe handling there too).
    """
    if inspect.iscoroutine(value):
        value.close()
    elif asyncio.isfuture(value):
        value.cancel()


def model_for(type_cls: type) -> type[models.Model]:
    """Return the Django model registered to a ``DjangoType``.

    Centralizes the ``type_cls.__django_strawberry_definition__.model`` lookup
    so every model-only read shares one source of truth with the
    queryset-variant seed below - the Relay node / id helpers, the connection
    total-order derive, the write pipeline's target-model reads, and the
    cascade-permission walk. Callers are responsible for ``type_cls`` being a
    registered ``DjangoType``; a missing definition surfaces as a raw
    ``AttributeError``.
    """
    return type_cls.__django_strawberry_definition__.model


def initial_queryset(type_cls: type) -> models.QuerySet:
    """Return ``model._default_manager.all()`` for a ``DjangoType``'s model.

    Step 1 of the Relay node defaults' four-step shape and the default
    resolver seed for list / connection fields. Seeds from
    ``model_for(type_cls)`` so the model lookup stays single-sited; every
    surface that needs a fresh unevaluated base queryset shares this one
    source. Callers are responsible for ``type_cls`` being a registered
    ``DjangoType``; a missing definition surfaces as a raw ``AttributeError``.
    """
    return model_for(type_cls)._default_manager.all()


def normalize_query_source(source: Any) -> tuple[Any, bool]:
    """Coerce a ``Manager`` to its ``QuerySet`` and report whether the result is one.

    The single Manager-to-QuerySet coercion shared by every resolver surface
    that accepts a consumer-supplied source (``DjangoListField`` /
    ``DjangoConnectionField`` consumer ``resolver=`` returns, the optimizer
    middleware's root return). A ``Manager`` (the ``Model.objects`` shorthand)
    becomes a fresh unevaluated ``QuerySet`` via ``.all()``; a ``QuerySet``
    passes through; a non-queryset iterable (a Python list / generator) passes
    through unchanged with ``is_queryset=False`` so the caller can short-circuit
    (pass it through, or raise its own GraphQL-specific error before pagination).

    Returns ``(source, is_queryset)`` rather than deciding the tail itself so
    each caller keeps its colored steps (``apply_type_visibility_*`` / the
    connection sidecar guard / the optimizer plan) explicit, never hidden behind
    a maybe-await abstraction.

    A ``Manager`` source is coerced through ``_coerced_manager_queryset``, which
    fails closed if the manager's ``.all()`` degrades into a non-queryset or
    silently changes the routed database - a Manager has explicitly selected the
    queryset / visibility path, so it must NEVER be allowed to fall into the
    plain-iterable (``is_queryset=False``) bypass reserved for a consumer that
    directly returns a list / generator.
    """
    if isinstance(source, models.Manager):
        return _coerced_manager_queryset(source), True
    return source, isinstance(source, models.QuerySet)


def coerce_field_value_or_none(field: models.Field, value: Any) -> Any:
    """Coerce ``value`` through ``field``'s ``to_python`` + ``run_validators``; ``None`` if invalid.

    The single "raw literal -> Django field value, or nothing" safety wrapper
    three independent call sites each grew their own copy of: the Relay
    ``GlobalID`` id-attr coercion (``relay.py::_coerce_pk_or_none``), the raw
    relation-pk coercion (``utils/write_values.py::coerce_relation_pk_or_none``),
    and the ``__in`` filter member coercion
    (``filters/base.py::_coerce_int_in_members``). ``to_python`` is a pure type
    cast that does NOT range-check, so a syntactically-valid but out-of-range
    literal (e.g. a pk past a backend's signed-64-bit column range) would
    otherwise reach a ``pk__in`` / ``filter`` call and raise a raw backend
    ``OverflowError`` (``Python int too large to convert to SQLite INTEGER``);
    the field's own validators (``integer_field_range`` Min/MaxValueValidators,
    etc.) reject it here as a ``ValidationError`` instead, and a non-numeric
    literal fails ``to_python`` itself. Every Django core field wraps its
    ``to_python`` failure in ``ValidationError`` already; ``TypeError`` /
    ``ValueError`` are caught too as a defensive superset for a field whose
    ``to_python`` raises one of those directly.

    Every caller treats ``None`` the same way - "identifies no row": dropped
    from a query, or mapped to a not-found / invalid sentinel - never a raw
    crash. WHICH field to coerce against is a genuine per-caller decision (a
    Relay type's resolved id field, a related model's pk, an arbitrary filtered
    column) and stays at each call site; only the coercion mechanics are
    single-sourced here.
    """
    try:
        coerced = field.to_python(value)
        field.run_validators(coerced)
    except (TypeError, ValueError, ValidationError):
        return None
    return coerced


_RELAY_ASYNC_RECOURSE = (
    "The Relay node defaults only await async get_queryset hooks on the async "
    "branch; either invoke the Relay node default from an async resolver, or "
    "redefine get_queryset as a sync method."
)


def sync_pipeline_recourse(flavor_noun: str) -> str:
    """Build the ``SyncMisuseError`` recourse a sync write pipeline appends (spec-039 Md2).

    The three write flavors (model / form / serializer) each raise a
    ``SyncMisuseError`` naming the SAME recourse when an ``async def get_queryset`` is
    met inside their (synchronous) ORM pipeline - byte-identical except the flavor
    subject. Single-sites that sentence so the three ``*_ASYNC_RECOURSE`` module
    constants cannot drift; each flavor still keeps its own named constant
    (``_MUTATION_ASYNC_RECOURSE`` / ``_FORM_ASYNC_RECOURSE`` /
    ``_SERIALIZER_ASYNC_RECOURSE``), now computed from this template. NOT used for the
    Relay recourse (``_RELAY_ASYNC_RECOURSE`` - async IS possible there) or the
    permission recourse (about ``has_permission`` / ``check_permission``, not
    ``get_queryset``), which are genuinely different wordings.
    """
    return (
        f"A {flavor_noun} runs its ORM pipeline synchronously (under one sync_to_async "
        "call on the async surface), so it cannot await an async get_queryset hook; "
        "redefine the target type's get_queryset as a sync method."
    )


async def run_in_one_sync_boundary(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Run ``fn(*args, **kwargs)`` in ONE ``sync_to_async(thread_sensitive=True)`` worker.

    The generic one-boundary primitive (spec-040 D17 / P3): every async surface
    that must keep a consumer-overridable sync hook (permission check, form
    filter body, cascade walk, mutation/form write pipeline, session auth) off
    the event loop shares this call, so the boundary discipline (one worker per
    resolution, ``thread_sensitive=True``, never per-step hops) cannot drift.
    A ``sync_to_async`` worker is itself a sync context, so the standing
    ``SyncMisuseError`` guards still fire inside ``fn``.

    Neutral home: lives here with the sibling ``reject_async_in_sync_context``
    primitive (cycle-safe utils substrate) rather than under ``mutations/``, so
    read-side modules (``filters/``, ``orders/``, root ``permissions.py``) can
    reuse it without a root-into-subpackage import.
    """
    return await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)


def _concrete_or_none(candidate: Any) -> type[models.Model] | None:
    """Return ``candidate._meta.concrete_model`` if ``candidate`` is a model, else ``None``.

    A hostile or malformed ``QuerySet.model`` / ``Query.model`` may be a
    non-model object (or missing entirely). Reading ``._meta.concrete_model``
    directly would leak a raw ``AttributeError`` past the boundary's typed
    error contract; this returns ``None`` for anything that is not a Django
    model so the caller can fail it closed as a table defect instead.
    """
    meta = getattr(candidate, "_meta", None)
    if meta is None:
        return None
    return getattr(meta, "concrete_model", None)


def _base_table_defect(query: Any, concrete: type[models.Model]) -> str | None:
    """Return the query's baked base table if it is not ``concrete``'s table.

    ``concrete`` is the registered type's ``_meta.concrete_model``, resolved once
    by the caller and threaded through (so a single seal walks the descriptor at
    most once rather than re-resolving it here).

    ``QuerySet.model`` and ``Query.model`` are mutable and are only what Django
    WILL consult to build the SQL alias map. Once that alias map is initialized
    the base table is frozen inside it, and reassigning the model attributes
    afterwards cannot change which table the SQL reads - so a hostile queryset
    can bake its alias map against one table, then spoof both model attributes
    to the registered type's model and pass a metadata-only check while still
    reading another table's rows. Read the authoritative base table straight
    from the initialized alias map (``Query.base_table`` ->
    ``alias_map[...].table_name``) and compare it to the concrete model's
    ``db_table``. An unbaked query (empty alias map) has no frozen table yet -
    ``Query.model`` still governs compilation and is validated separately by
    ``_combined_query_table_defect`` - so it returns ``None`` here.

    The base alias is recomputed from the FIRST key of ``alias_map`` rather than read
    from ``Query.base_table``: ``base_table`` is a ``@cached_property`` that can be
    poisoned in ``Query.__dict__`` to name a DIFFERENT alias than the one Django will
    use, and ``Query.clone`` deliberately DELETES that cache so the clone recomputes the
    first alias -- validation reading the poisoned cache would inspect one table while
    the cloned query compiles against another (``docs/feedback.md`` P1 ``base_table``).
    Iterating ``alias_map`` reproduces exactly what the cache-free clone does. The
    caller runs ``_query_ast_defect`` (which proves every ``alias_map`` join genuine and
    unshadowed) BEFORE this, so the ``.table_name`` read below dispatches no consumer
    code.
    """
    alias_map = getattr(query, "alias_map", None)
    if not alias_map:
        return None
    # The base table is the first alias (a ``BaseTable`` carrying ``table_name``) -- the
    # exact value ``Query.base_table`` recomputes after ``clone`` drops its cache.
    first_alias = next(iter(alias_map))
    table = alias_map[first_alias].table_name
    if table != concrete._meta.db_table:
        return table
    return None


def _type_is_genuinely_django(node_type: type) -> bool:
    """Return whether ``node_type`` is a genuine Django class by IDENTITY, not ``__module__``.

    Every clonable / compilable node embedded in a sealed ``sql.Query`` -- ``where``
    leaves and their operands, annotation / order-by / join expressions, subquery
    nodes -- must be a trusted Django implementation, because ``sql.Query.clone`` and
    the compiler dispatch that node's own ``clone`` / ``as_sql`` /
    ``resolve_expression`` while the seal is still deciding whether the graph is
    trusted (``docs/feedback.md`` P1-3). An earlier check trusted
    ``type(node).__module__.startswith("django.")`` -- but ``__module__`` is a plain
    writable string, so a consumer class declaring ``__module__ = "django.evil"``
    spoofed it (an adversarial review reproduced this). Provenance is therefore
    proven by OBJECT IDENTITY: the type must be the exact object Django itself
    exposes at ``sys.modules[module].<qualname>``. A consumer subclass, or a spoofed
    ``__module__`` / ``__qualname__`` pointing at a genuine name, cannot make
    ``getattr(genuine_django_module, name)`` return the consumer type, so it fails
    closed. A dotted (nested) qualname, or a module absent from ``sys.modules``, also
    fails closed. Exact genuine Django types only -- consumer-defined expressions /
    lookups are NOT supported across the visibility boundary.

    ``__module__`` and ``__qualname__`` are read through ``type.__getattribute__`` so a
    consumer METACLASS that overrides ``__getattribute__`` / ``__getattr__`` cannot run
    code (or return a lie) during the very read that is meant to reject the type
    (``docs/feedback.md`` P2 metaclass): ``type.__getattribute__`` resolves both names
    from the class's own namespace without dispatching a metaclass hook.
    """
    try:
        module_name = type.__getattribute__(node_type, "__module__")
        qualname = type.__getattribute__(node_type, "__qualname__")
    except (AttributeError, TypeError):
        return False
    if type(module_name) is not str or not module_name.startswith("django."):
        return False
    if type(qualname) is not str or "." in qualname:
        return False
    module = sys.modules.get(module_name)
    if module is None:
        return False
    return getattr(module, qualname, None) is node_type


# Inert query-parameter leaf types: a bound value the compiler renders as ``%s`` with
# the value as a parameter, never dispatching an ``as_sql`` / ``resolve_expression``
# the seal would have to trust. These terminate the genuineness walk. A model
# instance is handled separately (only legal as a deferred-filter value, where Django
# extracts its pk to a bound parameter -- ``related_descriptors.py`` ``core_filters``).
# Membership is tested by EXACT type, never ``isinstance``: a ``str`` / ``int`` /
# ``datetime`` SUBCLASS can define ``resolve_expression`` (or an ``as_sql``) and would
# then be dispatched by ``add_q`` / the compiler, so a subclass is NOT inert and must
# prove genuine-Django provenance like any other object (``docs/feedback.md`` P1
# inert-subclass). ``datetime.datetime`` is listed explicitly because exact-type
# membership no longer inherits it from ``datetime.date``.
_INERT_VALUE_TYPES: frozenset[type] = frozenset(
    {
        str,
        bytes,
        bytearray,
        bool,
        int,
        float,
        complex,
        Decimal,
        datetime.datetime,
        datetime.date,
        datetime.time,
        datetime.timedelta,
        uuid.UUID,
    },
)


def _is_inert_value(value: Any) -> bool:
    """Return whether ``value`` is an inert (non-dispatchable) query-parameter leaf.

    ``None`` is inert. Membership is by EXACT type, so a ``str`` / ``int`` /
    ``datetime`` SUBCLASS carrying a ``resolve_expression`` / ``as_sql`` is NOT treated
    as inert (``docs/feedback.md`` P1 inert-subclass) -- it falls through to the
    genuine-Django provenance walk and fails closed. Anything else is a container
    (walked member-wise) or an object that must prove provenance before the seal lets
    the compiler dispatch it.
    """
    return value is None or type(value) in _INERT_VALUE_TYPES


def _shadow_defect(node: Any, label: str) -> tuple[str, str] | None:
    """Return a defect if ``node``'s instance ``__dict__`` shadows a callable method.

    Python methods are non-data descriptors, so an instance-``__dict__`` entry named
    after a class method wins over the genuine method even when ``type(node)`` is
    exactly the expected class (``docs/feedback.md`` P1-1). ``sql.Query.clone`` and
    the compiler dispatch bound methods -- ``where.clone()``, an expression's
    ``as_sql`` -- so ANY ``__dict__`` key naming a callable attribute of the node's
    (already-proven-genuine) type fails closed. A non-string ``__dict__`` key is
    itself anomalous (Django never produces one) and would otherwise raise
    ``TypeError`` out of ``getattr`` past the typed contract, so it fails closed
    first. Read straight from ``__dict__`` so a shadow cannot hide itself; only ever
    called after the node's type is proven genuine (or exactly ``WhereNode`` /
    ``sql.Query``), so the ``getattr`` against that type dispatches no consumer code.

    Two wordings distinguish the canonical emitter from the dynamically-resolved
    per-vendor ones. ``as_sql`` is the fixed base compile method every ``Expression``
    defines, and any other callable class attribute a shadow overrides (``clone`` /
    ``resolve_expression`` / ...) is likewise a concrete method, so both read "shadows
    the ``<name>`` method". An instance key beginning ``as_`` OTHER than ``as_sql``
    reads "shadows the ``<name>`` compiler method": the compiler resolves the
    per-backend emitter DYNAMICALLY as ``getattr(node, "as_" + connection.vendor,
    node.as_sql)`` (``as_sqlite`` / ``as_postgresql`` / ...), so a shadow named for a
    vendor -- even one a mixin defines on this class (``SQLiteNumericMixin.as_sqlite``)
    -- gets dispatched at compile time through that dynamic lookup rather than the
    fixed ``as_sql`` slot (``docs/feedback.md`` P1 vendor ``as_``). The vendor-prefix
    check therefore runs BEFORE the callable-class-attribute check so a mixin-provided
    ``as_<vendor>`` still takes the "compiler method" wording. Genuine Django nodes
    never carry an ``as_*`` INSTANCE attribute (their emitters are class methods), so
    rejecting the prefix costs no legitimate query.
    """
    node_dict = object.__getattribute__(node, "__dict__")
    node_type = type(node)
    for key in node_dict:
        if type(key) is not str:
            return ("untrusted", f"{label} has a non-string __dict__ key")
        if key.startswith("as_") and key != "as_sql":
            return ("untrusted", f"{label} shadows the {key!r} compiler method")
        if key == "as_sql" or callable(getattr(node_type, key, None)):
            return ("untrusted", f"{label} shadows the {key!r} method")
    return None


# SQL-template metadata a genuine Django expression interpolates DIRECTLY into the
# emitted SQL string during ``as_sql`` -- never routed through ``get_source_expressions``
# and never bound as a ``%s`` parameter. ``Func`` joins its argument SQL with
# ``self.arg_joiner.join(...)`` and formats ``self.template % {"function": self.function,
# ...}``; ``CombinedExpression`` interpolates ``self.connector``; ``RawSQL`` emits
# ``self.sql`` verbatim. An EXACT genuine node whose instance ``__dict__`` overrides one
# of these with a non-``str`` object would run that object's ``join`` / ``__str__`` at
# compile time (``docs/feedback.md`` P1 Func metadata), so each override present on the
# instance must be exactly ``str``. Genuine Django only ever stores strings here.
_SQL_TEMPLATE_ATTRS: tuple[str, ...] = (
    "template",
    "function",
    "arg_joiner",
    "connector",
    "sql",
    "base_template",
)


def _node_metadata_defect(node: Any, label: str) -> tuple[str, str] | None:
    """Return a defect for compiler-reachable node metadata NOT covered by source expressions.

    ``get_source_expressions`` enumerates the operand sub-expressions the compiler
    recurses, but ``Func.as_sql`` (and its cousins) ALSO interpolate formatting metadata
    the old walk never validated (``docs/feedback.md`` P1 -- the exact ``Func`` schema
    gap): each ``_SQL_TEMPLATE_ATTRS`` name present on the instance ``__dict__`` must be
    an exact ``str``, because it is formatted straight into the SQL string (``template %
    data``) or used as a ``.join`` separator, so a non-``str`` override would run that
    object's ``__str__`` / ``join`` at compile time.

    ``node`` is proven an EXACT genuine Django expression type before this runs, so these
    attributes are Django's own string defaults unless the instance ``__dict__`` shadows
    them; genuine Django never stores a non-string there, so the check costs no
    legitimate query. ``output_field`` is deliberately NOT constrained to a Django-owned
    type here: a ``Col``'s ``output_field`` is the queried model's OWN field, which may
    legitimately be a consumer-defined ``models.Field`` subclass (part of the trusted
    schema, not injected by the hook) -- its shadow / ``as_`` surface is already covered
    when the field itself is reached, and forcing it Django-owned would fail-close every
    query over a custom model field.
    """
    node_dict = object.__getattribute__(node, "__dict__")
    for attr in _SQL_TEMPLATE_ATTRS:
        if attr in node_dict and type(node_dict[attr]) is not str:
            return ("untrusted", f"{label} {attr} is a {type(node_dict[attr]).__name__}")
    return None


def _expr_graph_defect(node: Any, seen: set[int], label: str) -> tuple[str, str] | None:
    """Return the first non-genuine / shadowed node in an expression graph, or ``None``.

    The single recursive, identity-memoized traversal of every compiler-reachable
    node hanging off one expression slot (a ``where`` leaf, an annotation value, an
    ``order_by`` element). It replaces the old top-level-only inventory
    (``docs/feedback.md`` Finding H / P1-3): each node must be an inert value, a plain
    container walked member-wise, an EXACT ``WhereNode`` subtree, or an EXACT genuine
    Django expression that is unshadowed AND whose own operands
    (``get_source_expressions``) and any inner ``Subquery`` recurse under the same
    rule. ``seen`` (node ``id``) collapses a shared expression diamond to a single
    visit and stops a cyclic graph, keeping the walk linear in the graph's unique
    node count.
    """
    if _is_inert_value(node):
        return None
    node_type = type(node)
    if node_type in (
        list,
        tuple,
        set,
        frozenset,
    ):
        # Containers memoize too: a self-referential list / dict would otherwise
        # recurse without bound and escape as a raw ``RecursionError`` past the
        # typed defect contract, instead of terminating like a shared diamond.
        node_id = id(node)
        if node_id in seen:
            return None
        seen.add(node_id)
        for item in node:
            defect = _expr_graph_defect(item, seen, label)
            if defect is not None:
                return defect
        return None
    if node_type is dict:
        node_id = id(node)
        if node_id in seen:
            return None
        seen.add(node_id)
        for key, value in node.items():
            if type(key) is not str:
                return ("untrusted", f"{label} has a non-string mapping key")
            defect = _expr_graph_defect(value, seen, label)
            if defect is not None:
                return defect
        return None
    # ``WhereNode`` and ``sql.Query`` (a subquery's inner query, surfaced by
    # ``Subquery.get_source_expressions``) route to their dedicated walkers BEFORE this
    # level touches ``seen`` -- those walkers own the memoization for their node, so
    # pre-adding the id here would make their own ``id in seen`` guard short-circuit and
    # skip the subtree (a hostile leaf inside a subquery ``where`` would then escape).
    if node_type is WhereNode:
        return _where_tree_defect(node, seen)
    if node_type is sql.Query:
        return _query_genuineness_defect(node, seen)
    node_id = id(node)
    if node_id in seen:
        return None
    seen.add(node_id)
    if not _type_is_genuinely_django(node_type):
        return ("untrusted", f"{label} carries a {node_type.__name__} node")
    shadow = _shadow_defect(node, label)
    if shadow is not None:
        return shadow
    metadata_defect = _node_metadata_defect(node, label)
    if metadata_defect is not None:
        return metadata_defect
    if getattr(node_type, "get_source_expressions", None) is not None:
        for child in node.get_source_expressions():
            defect = _expr_graph_defect(child, seen, label)
            if defect is not None:
                return defect
    # A ``Subquery`` / ``Exists`` surfaces its wrapped inner ``sql.Query`` through
    # ``get_source_expressions`` (verified for every genuine Django subquery node), so
    # the loop above already routes that inner query to ``_query_genuineness_defect``
    # (via the ``node_type is sql.Query`` branch) and recurses its whole graph -- a
    # foreign inner ``Query`` subclass or a buried consumer expression fails closed
    # there (``test_hostile_subquery_inner_query_fails_closed`` /
    # ``test_hostile_expression_inside_genuine_subquery_where_fails_closed``). No
    # separate subquery re-walk is needed; adding one would be dead, unreachable code
    # because ``get_source_expressions`` front-validates the same inner query.
    return None


def _expr_sequence_defect(holder: Any, seen: set[int], label: str) -> tuple[str, str] | None:
    """Return a defect for an ``order_by`` / ``group_by`` / ``select`` sequence, or ``None``.

    These slots hold a mix of plain field-reference strings (safe) and expressions
    the compiler dispatches ``as_sql`` on. ``None`` and a bare ``bool`` (``group_by``
    is ``True`` / ``False`` for the default cases) carry no node. Every non-string
    element recurses through ``_expr_graph_defect`` so a consumer ``order_by``
    expression (never walked before -- ``docs/feedback.md`` Finding 3) fails closed.
    """
    if holder is None or type(holder) is bool:
        return None
    if type(holder) not in (list, tuple):
        return ("untrusted", f"query {label} is a {type(holder).__name__}")
    for item in holder:
        if type(item) is str:
            continue
        defect = _expr_graph_defect(item, seen, label)
        if defect is not None:
            return defect
    return None


def _raw_sql_sequence_defect(holder: Any, label: str) -> tuple[str, str] | None:
    """Return a defect for an ``extra_order_by`` / ``extra_tables`` sequence, or ``None``.

    The ``.extra()`` raw-SQL slots the compiler emits VERBATIM (never compiled through an
    expression's ``as_sql``): ``extra_order_by`` fragments become ``ORDER BY`` text and
    ``extra_tables`` become ``FROM`` aliases. The old walk never touched them
    (``docs/feedback.md`` P1 ``extra_order_by``), so a non-``str`` element -- an object
    whose ``__str__`` runs at SQL-assembly time -- or a sequence SUBCLASS with a stateful
    ``__iter__`` escaped. Django only ever stores an exact ``tuple`` / ``list`` of exact
    ``str`` here; anything else fails closed.
    """
    if holder is None:
        return None
    if type(holder) not in (tuple, list):
        return ("untrusted", f"query {label} is a {type(holder).__name__}")
    for item in holder:
        if type(item) is not str:
            return ("untrusted", f"query {label} carries a {type(item).__name__}")
    return None


def _join_defect(join: Any, alias: str, seen: set[int]) -> tuple[str, str] | None:
    """Return a defect if an ``alias_map`` join is not a genuine, unshadowed Django join.

    ``sql.Query.clone`` shallow-copies ``alias_map`` (sharing the join objects) and
    the compiler later dispatches each join's ``as_sql`` / ``relabeled_clone``, so a
    consumer ``Join`` subclass -- or an exact ``BaseTable`` / ``Join`` with a shadowed
    method -- would run at compile time. Exact genuine Django join types only.

    A ``Join`` produced by ``.filter()`` over a ``FilteredRelation`` (Django's
    ``FilteredRelation`` / ``FILTERED_RELATION``) carries ``join.filtered_relation``,
    whose ``resolved_condition`` (a ``WhereNode``) the compiler dispatches from
    ``Join.as_sql`` -> ``FilteredRelation.as_sql`` (``docs/feedback.md`` P1
    ``filtered_relation``). That condition is NOT reachable from ``alias_map`` alone, so
    when present the filtered relation must itself be genuine + unshadowed and its
    resolved condition must pass the ``where``-tree walk; otherwise a consumer
    expression buried there would strip / rewrite the visibility predicate at compile
    time. ``seen`` is shared so a condition reachable two ways is walked once.
    """
    if not _type_is_genuinely_django(type(join)):
        return ("untrusted", f"join for alias {alias!r} is a {type(join).__name__}")
    join_shadow = _shadow_defect(join, f"join for alias {alias!r}")
    if join_shadow is not None:
        return join_shadow
    filtered = getattr(join, "filtered_relation", None)
    if filtered is None:
        return None
    if not _type_is_genuinely_django(type(filtered)):
        return (
            "untrusted",
            f"join for alias {alias!r} filtered_relation is a {type(filtered).__name__}",
        )
    filtered_shadow = _shadow_defect(filtered, f"join for alias {alias!r} filtered_relation")
    if filtered_shadow is not None:
        return filtered_shadow
    resolved = getattr(filtered, "resolved_condition", None)
    if resolved is None:
        return None
    return _where_tree_defect(resolved, seen)


def _where_tree_defect(node: Any, seen: set[int]) -> tuple[str, str] | None:
    """Return the first non-genuine / shadowed node in a ``where`` tree, or ``None``.

    ``sql.Query.clone`` calls ``self.where.clone()``, which dispatches
    ``child.clone()`` on every child, so a consumer ``WhereNode`` subclass -- OR an
    EXACT ``WhereNode`` whose instance ``__dict__`` shadows ``clone`` -- would run
    during sealing and strip the visibility predicate (``docs/feedback.md`` P1-3, and
    the exact-``WhereNode`` shadow vector an adversarial review reproduced: the
    shadowed ``clone`` fired mid-seal and the sealed SQL lost its ``WHERE``). Every
    internal node must be EXACTLY ``WhereNode`` and unshadowed; every leaf and every
    leaf operand recurses through ``_expr_graph_defect`` so a consumer expression in
    lookup-RHS position (Finding H) or a shadowed ``as_sql`` on an exact Django leaf
    also fails closed.
    """
    if type(node) is not WhereNode:
        return _expr_graph_defect(node, seen, "where clause")
    node_id = id(node)
    if node_id in seen:
        return None
    seen.add(node_id)
    shadow = _shadow_defect(node, "where node")
    if shadow is not None:
        return shadow
    node_dict = object.__getattribute__(node, "__dict__")
    # ``WhereNode.as_sql`` interpolates ``self.connector`` (``AND`` / ``OR``) straight
    # into the emitted SQL, so an instance override with a non-``str`` connector would
    # run its ``__str__`` at compile time (``docs/feedback.md`` P1 node metadata).
    connector = node_dict.get("connector")
    if connector is not None and type(connector) is not str:
        return ("untrusted", f"where node connector is a {type(connector).__name__}")
    children = node_dict.get("children")
    if children is not None and type(children) not in (list, tuple):
        return ("untrusted", f"where node children is a {type(children).__name__}")
    for child in children or ():
        child_defect = _where_tree_defect(child, seen)
        if child_defect is not None:
            return child_defect
    return None


def _select_related_defect(select_related: Any) -> tuple[str, str] | None:
    """Return a defect if ``select_related`` is not a plain bool / str-keyed dict tree.

    ``sql.Query.clone`` ``deepcopy``s ``select_related`` when it is not ``False``.
    Django only ever stores a bool or a nested ``{str: {str: ...}}`` dict there, so
    any other object (or a non-string key / non-dict value) is a consumer-injected
    structure whose ``__deepcopy__`` would dispatch during sealing; it fails closed
    as ``untrusted`` (``docs/feedback.md`` P1-3).
    """
    if isinstance(select_related, bool):
        return None
    if type(select_related) is not dict:
        return ("untrusted", f"select_related is a {type(select_related).__name__}")
    for key, value in select_related.items():
        if type(key) is not str:
            return ("untrusted", f"select_related key is a {type(key).__name__}")
        nested_defect = _select_related_defect(value)
        if nested_defect is not None:
            return nested_defect
    return None


# Query containers ``sql.Query.clone`` calls ``.copy()`` on (dicts / sets) or
# ``deepcopy``s. Each must be EXACTLY the builtin Django uses so ``clone`` dispatches
# only builtin methods, never a consumer ``dict`` / ``set`` SUBCLASS ``.copy()`` (an
# adversarial review reproduced a custom ``alias_refcount.copy()`` firing mid-clone).
_EXACT_DICT_QUERY_ATTRS: tuple[str, ...] = (
    "alias_refcount",
    "alias_map",
    "external_aliases",
    "table_map",
    "annotations",
    "extra",
    "_filtered_relations",
)
_EXACT_SET_QUERY_ATTRS: tuple[str, ...] = (
    "annotation_select_mask",
    "extra_select_mask",
    "used_aliases",
    "subq_aliases",
)


def _query_container_defect(query: Any) -> tuple[str, str] | None:
    """Return a defect if any container ``sql.Query.clone`` copies is not an exact builtin.

    ``Query.clone`` calls ``.copy()`` on ``alias_refcount`` / ``alias_map`` /
    ``external_aliases`` / ``table_map`` / ``annotations`` / ``extra`` /
    ``_filtered_relations`` (dicts), on the ``annotation_select_mask`` /
    ``extra_select_mask`` / ``used_aliases`` / ``subq_aliases`` (sets), and on
    ``_extra_select_cache`` (dict). A consumer ``dict`` / ``set`` SUBCLASS with an
    overridden ``.copy()`` -- or a non-string mapping key that later raises out of
    ``getattr`` past the typed contract -- would dispatch consumer code during
    cloning, so each is required to be EXACTLY the builtin. Validates the object
    ATTRIBUTE ACCESS returns (what ``clone`` calls ``.copy()`` on -- a class default
    like ``subq_aliases`` lives off the instance ``__dict__``); the query is already
    proven exactly ``sql.Query`` and shadow-checked, so the reads run no consumer code.

    ``combined_queries`` (the ``.union()`` / ``.intersection()`` / ``.difference()``
    branch tuple) is required to be an EXACT ``tuple`` before any branch is walked:
    ``Query.clone`` rebuilds it as ``tuple(q.clone() for q in self.combined_queries)``,
    re-ITERATING it, so a ``tuple`` SUBCLASS with a stateful ``__iter__`` could yield
    ``concrete``'s branches during validation and a foreign model's branches during the
    clone / compile (``docs/feedback.md`` P1 ``combined_queries``). An exact tuple's
    iteration is deterministic, so validation and execution see identical branches.
    """
    for attr in _EXACT_DICT_QUERY_ATTRS:
        value = getattr(query, attr, None)
        if value is None:
            continue
        if type(value) is not dict:
            return ("untrusted", f"query {attr} is a {type(value).__name__}")
        for key in value:
            if type(key) is not str:
                return ("untrusted", f"query {attr} has a non-string key")
    for attr in _EXACT_SET_QUERY_ATTRS:
        value = getattr(query, attr, None)
        if value is not None and type(value) not in (set, frozenset):
            return ("untrusted", f"query {attr} is a {type(value).__name__}")
    cache = getattr(query, "_extra_select_cache", None)
    if cache is not None and type(cache) is not dict:
        return ("untrusted", f"query _extra_select_cache is a {type(cache).__name__}")
    combined = getattr(query, "combined_queries", None)
    if combined is not None and type(combined) is not tuple:
        return ("untrusted", f"query combined_queries is a {type(combined).__name__}")
    return None


def _query_ast_defect(query: Any, seen: set[int]) -> tuple[str, str] | None:
    """Return the first untrusted embedded AST node in ``query``, or ``None``.

    The complete genuineness walk over EVERY compiler-reachable expression slot the
    old inventory missed (``docs/feedback.md`` Finding H / Finding 3): the ``where``
    and ``having`` trees and their leaf operands, ``annotations`` values (recursively,
    including nested ``Func`` / ``Case`` operands and inner ``Subquery`` graphs),
    the ``order_by`` / ``group_by`` / ``distinct_fields`` / ``select`` /
    ``values_select`` sequences, the ``alias_map`` joins (and any join's
    ``filtered_relation`` condition), the ``extra_order_by`` / ``extra_tables`` raw-SQL
    sequences (emitted verbatim by the compiler -- ``docs/feedback.md`` P1
    ``extra_order_by``), and the ``select_related`` structure. ``query`` is only ever
    passed here after the caller proved it is EXACTLY ``sql.Query`` and shadow-checked,
    so attribute access dispatches no consumer code and correctly returns class-default
    slots (``select_related`` is ``False``, ``order_by`` is ``()``) that never reach the
    instance ``__dict__``; ``seen`` is shared across every slot so a node reachable two
    ways is walked once.
    """
    where_defect = _where_tree_defect(getattr(query, "where", None), seen)
    if where_defect is not None:
        return where_defect
    having = getattr(query, "having", None)
    if having is not None:
        having_defect = _where_tree_defect(having, seen)
        if having_defect is not None:
            return having_defect
    for name, expr in (getattr(query, "annotations", None) or {}).items():
        annotation_defect = _expr_graph_defect(expr, seen, f"annotation {name!r}")
        if annotation_defect is not None:
            return annotation_defect
    for label in (
        "order_by",
        "group_by",
        "distinct_fields",
        "select",
        "values_select",
    ):
        sequence_defect = _expr_sequence_defect(getattr(query, label, None), seen, label)
        if sequence_defect is not None:
            return sequence_defect
    for label in ("extra_order_by", "extra_tables"):
        raw_defect = _raw_sql_sequence_defect(getattr(query, label, None), label)
        if raw_defect is not None:
            return raw_defect
    for alias, join in (getattr(query, "alias_map", None) or {}).items():
        join_defect = _join_defect(join, alias, seen)
        if join_defect is not None:
            return join_defect
    return _select_related_defect(getattr(query, "select_related", False))


def _query_genuineness_defect(query: Any, seen: set[int]) -> tuple[str, str] | None:
    """Return the first genuineness defect in ``query`` (NO concrete-table check), or ``None``.

    A ``Subquery`` / ``Exists`` legitimately targets ANOTHER table, so only the
    genuineness half of ``_combined_query_table_defect`` applies to its embedded
    query -- every node it reaches must be genuine, unshadowed, and exact-builtin
    shaped so its clone / compile dispatch is trusted, but its base table is not
    required to be the outer concrete model. Fails closed unless the embedded query
    is EXACTLY ``sql.Query``; shares the caller's ``seen`` set and recurses combined
    branches under the same rule.
    """
    if type(query) is not sql.Query:
        return ("untrusted", f"embedded query is a {type(query).__name__}")
    query_id = id(query)
    if query_id in seen:
        return None
    seen.add(query_id)
    shadow_defect = _shadow_defect(query, "subquery instance")
    if shadow_defect is not None:
        return shadow_defect
    container_defect = _query_container_defect(query)
    if container_defect is not None:
        return container_defect
    ast_defect = _query_ast_defect(query, seen)
    if ast_defect is not None:
        return ast_defect
    for branch in getattr(query, "combined_queries", ()) or ():
        branch_defect = _query_genuineness_defect(branch, seen)
        if branch_defect is not None:
            return branch_defect
    return None


def _combined_query_table_defect(
    query: Any,
    concrete: type[models.Model],
) -> tuple[str, str] | None:
    """Return the first contributing-table / genuineness / foreign-branch defect, or ``None``.

    ``concrete`` is the registered type's ``_meta.concrete_model``, resolved once by
    the caller and threaded through the recursion (and into ``_base_table_defect``) so
    a single seal never re-walks that descriptor. This is the one place that proves,
    of a candidate ``sql.Query`` (and every combined branch), BOTH that it contributes
    only ``concrete``'s table AND that its whole clonable / compilable graph is trusted
    to dispatch:

    - ``Query.model`` may disagree with the public ``QuerySet.model`` (both are
      mutable); the SQL-bearing ``Query.model`` is validated directly. A ``None`` or
      non-model ``Query.model`` fails closed as a table defect -- a model-row select
      query with no model compiles to ``SELECT  FROM ...`` and escapes as malformed
      SQL otherwise (``docs/feedback.md`` P2-1).
    - Any callable ``sql.Query`` method shadowed on the instance ``__dict__`` is
      rejected (``_shadow_defect``), and every container ``sql.Query.clone`` copies is
      required to be an exact builtin (``_query_container_defect``) -- both before the
      clone, because ``clone`` shallow-copies ``__dict__`` and calls ``.copy()`` /
      ``deepcopy`` on those containers (``docs/feedback.md`` P1-1).
    - Every compiler-reachable embedded node (the ``where`` / ``having`` trees and
      their operands, ``annotations``, ``order_by`` / ``group_by`` / ``select`` /
      ``distinct`` sequences, ``alias_map`` joins, subquery graphs, ``select_related``)
      is proven a genuine, unshadowed Django implementation by ``_query_ast_defect``
      before the clone dispatches its ``clone`` / the compiler dispatches its
      ``as_sql`` (``docs/feedback.md`` P1-3 / Finding H / Finding 3).
    - The alias map, once initialized, is the authoritative base table and can
      disagree with a since-reassigned ``Query.model`` -- ``_base_table_defect``
      catches that.
    - A combined queryset (``.union()`` / ``.intersection()`` / ``.difference()``)
      reports the outer model on ``QuerySet.model`` while a branch ``Query`` reads
      another model's table; with compatible projections the branch rows materialize
      as the outer model, so another table's rows would cross the boundary. Every
      ``combined_queries`` branch is recursed with the same checks, and a branch whose
      ``type(branch)`` is not exactly ``sql.Query`` is a foreign ``Query`` SUBCLASS
      whose consumer-overridable SQL synthesis fails closed as ``untrusted``.

    Returns ``(code, detail)`` -- ``code`` in ``{"table", "untrusted"}`` -- for the
    first offending branch, or ``None`` when every contributing table is
    ``concrete``'s table and the whole graph is trusted. A fresh ``seen`` set backs
    each top-level call so a shared expression diamond is walked once.
    """
    query_model = getattr(query, "model", None)
    if _concrete_or_none(query_model) is not concrete:
        return ("table", getattr(query_model, "__name__", type(query_model).__name__))
    shadow_defect = _shadow_defect(query, "query instance")
    if shadow_defect is not None:
        return shadow_defect
    container_defect = _query_container_defect(query)
    if container_defect is not None:
        return container_defect
    # The AST walk runs BEFORE the base-table check: it proves every ``alias_map`` join
    # is a genuine, unshadowed Django join, so ``_base_table_defect`` can then read the
    # first join's ``.table_name`` without dispatching consumer code.
    ast_defect = _query_ast_defect(query, set())
    if ast_defect is not None:
        return ast_defect
    base_defect = _base_table_defect(query, concrete)
    if base_defect is not None:
        return ("table", base_defect)
    for branch in getattr(query, "combined_queries", ()) or ():
        if type(branch) is not sql.Query:
            return ("untrusted", f"combined-query branch is {type(branch).__name__}")
        defect = _combined_query_table_defect(branch, concrete)
        if defect is not None:
            return defect
    return None


# Django's own row-iterable classes. A sealed queryset may only carry one of
# these as its ``_iterable_class``: ``ModelIterable`` yields model instances,
# the four ``Values*`` classes yield the dict / tuple / namedtuple / flat shapes
# of ``.values()`` / ``.values_list()``. Anything else is a consumer-supplied
# row synthesizer (the ``.first()`` / ``.__aiter__()`` synthetic-row vector the
# review reproduced) and cannot be sealed.
_DJANGO_ITERABLE_CLASSES: frozenset[type] = frozenset(
    {
        ModelIterable,
        ValuesIterable,
        ValuesListIterable,
        NamedValuesListIterable,
        FlatValuesListIterable,
    },
)


def _rebuilt_prefetch_or_defect(
    entry: Prefetch,
    cls_name: str,
    sealed_inner: models.QuerySet | None,
) -> tuple[Prefetch | None, tuple[str, str] | None]:
    """Rebuild a validated ``Prefetch`` as an EXACT ``django.db.models.Prefetch``.

    Every ``Prefetch`` -- including the ``queryset=None`` case -- is rebuilt from
    scratch so a consumer ``Prefetch`` subclass cannot survive with an executable
    ``get_current_querysets`` override that substitutes an unsealed child at fetch
    time (``docs/feedback.md`` P1-4a). Only the exact-``str`` /
    ``None`` path state Django itself stores (``prefetch_through``,
    ``prefetch_to``, ``to_attr``) is copied forward; a subclass-injected extra
    attribute or a non-``str`` path fails closed as ``untrusted``.
    """
    entry_state = object.__getattribute__(entry, "__dict__")
    through = entry_state.get("prefetch_through")
    prefetch_to = entry_state.get("prefetch_to")
    to_attr = entry_state.get("to_attr")
    if type(through) is not str or type(prefetch_to) is not str:
        return None, ("untrusted", f"{cls_name} prefetch path is not an exact str")
    if to_attr is not None and type(to_attr) is not str:
        return None, ("untrusted", f"{cls_name} prefetch to_attr is not an exact str or None")
    rebuilt = Prefetch.__new__(Prefetch)
    rebuilt_state = object.__getattribute__(rebuilt, "__dict__")
    rebuilt_state["prefetch_through"] = through
    rebuilt_state["prefetch_to"] = prefetch_to
    rebuilt_state["to_attr"] = to_attr
    rebuilt_state["queryset"] = sealed_inner
    return rebuilt, None


def _sealed_prefetch_related_lookups(
    lookups: Any,
    cls_name: str,
    required_alias: str | None,
) -> tuple[tuple[Any, ...] | None, tuple[str, str] | None]:
    """Seal every ``Prefetch`` entry's inner queryset; pass string lookups through.

    ``_prefetch_related_lookups`` entries are either plain string lookups (safe --
    Django builds the related queryset itself) or ``django.db.models.Prefetch``
    objects. A ``Prefetch`` carrying a consumer ``.queryset`` is the one-level-down
    leak vector the seal must close: at evaluation Django dispatches into that
    queryset's own ``_fetch_all`` / ``__iter__`` to populate the related
    descriptor, so a hostile ``QuerySet`` subclass could seed a synthetic
    in-memory row the SQL never selected and no visibility hook ever saw --
    defeating the seal's "never dispatch consumer code / never return synthetic
    rows" guarantee one edge down the object graph.

    Each such inner queryset is recursively sealed through ``_seal_or_defect``
    against its OWN declared model (read via ``__dict__``, never a shadowable
    descriptor) and rebuilt into a fresh plain ``Prefetch`` -- the subclass
    identity of both the inner queryset AND the ``Prefetch`` wrapper is dropped,
    so neither a hostile queryset override nor a hostile ``Prefetch`` method
    override can re-inject at fetch time. The child seal runs with
    ``allow_sliced=True`` because a sliced prefetch queryset is legal (Django >=
    4.2 top-N per parent) and nothing refilters a prefetch child, while
    ``require_model_rows`` still holds. A child that cannot be sealed (a
    non-queryset ``.queryset``, a malformed model, a foreign ``Query`` class, a
    foreign row iterable, a subclass carrying an unresolved deferred filter) fails
    the OUTER seal closed with the ``untrusted`` defect -- carrying the inner
    child's own ``(code: detail)`` in the message rather than a generic string --
    rather than being silently dropped. A ``Prefetch`` whose ``.queryset is None``
    (Django builds the child itself) and a plain string lookup both pass through
    unchanged.

    Returns ``(sealed_lookups, None)`` on success or ``(None, (code, detail))``
    on the first unsealable child.
    """
    # ``_prefetch_related_lookups`` must be an exact ``tuple`` / ``list`` before it is
    # iterated: Django stores an exact tuple, and a consumer object with a custom
    # ``__bool__`` / ``__iter__`` would otherwise dispatch on the truthiness test / the
    # loop below (``docs/feedback.md`` P2 retained-state).
    if lookups is None:
        return (), None
    if type(lookups) not in (tuple, list):
        return None, ("untrusted", f"{cls_name} prefetch lookups is a {type(lookups).__name__}")
    sealed_entries: list[Any] = []
    for entry in lookups:
        if not isinstance(entry, Prefetch):
            # A non-``Prefetch`` lookup must be EXACTLY ``str`` (Django builds the
            # related queryset itself); a ``str`` subclass or arbitrary lookup
            # object retains method dispatch and fails closed (``docs/feedback.md``
            # P1-4a).
            if type(entry) is not str:
                return None, (
                    "untrusted",
                    f"{cls_name} prefetch lookup is a {type(entry).__name__}",
                )
            sealed_entries.append(entry)
            continue
        entry_state = object.__getattribute__(entry, "__dict__")
        inner = entry_state.get("queryset")
        sealed_inner: models.QuerySet | None = None
        if inner is not None:
            inner_state = (
                object.__getattribute__(inner, "__dict__")
                if isinstance(inner, models.QuerySet)
                else None
            )
            if inner_state is None or _concrete_or_none(inner_state.get("model")) is None:
                lookup = entry_state.get("prefetch_through")
                return None, (
                    "untrusted",
                    f"{cls_name} prefetch {lookup!r} queryset cannot be sealed",
                )
            # Thread the OUTER effective alias into the child seal with
            # ``require_shared_alias=True``: a child explicitly pinned to a DIFFERENT
            # alias fails closed (the seal's ``alias`` defect), and -- critically --
            # when the outer alias is UNRESOLVED (``effective_alias is None`` because
            # the parent is unrouted), an explicitly routed child ALSO fails closed
            # rather than being accepted onto a divergent database, so one GraphQL
            # resolution never schedules the parent and its related rows across two
            # connections (``docs/feedback.md`` P1-4b). An unrouted child inherits the
            # outer alias.
            # Prefetch children may legally be sliced (Django >= 4.2 top-N per
            # parent, e.g. ``Prefetch("items", queryset=Item.objects.all()[:5])``):
            # nothing refilters / reorders a prefetch child, so the ``sliced``
            # rejection (which exists because outer read surfaces refilter) does
            # not apply one edge down, while ``require_model_rows`` still holds
            # (Django itself requires a ``ModelIterable`` for a prefetch queryset).
            sealed_inner, defect = _seal_or_defect(
                inner,
                inner_state.get("model"),
                required_alias,
                require_model_rows=True,
                allow_sliced=True,
                require_shared_alias=True,
            )
            if defect is not None:
                lookup = entry_state.get("prefetch_through")
                code, detail = defect
                return None, (
                    "untrusted",
                    f"{cls_name} prefetch {lookup!r} queryset cannot be sealed ({code}: {detail})",
                )
        rebuilt, rebuild_defect = _rebuilt_prefetch_or_defect(entry, cls_name, sealed_inner)
        if rebuild_defect is not None:
            return None, rebuild_defect
        sealed_entries.append(rebuilt)
    return tuple(sealed_entries), None


def _deferred_value_defect(value: Any, seen: set[int], label: str) -> tuple[str, str] | None:
    """Return a defect if a deferred-filter value is neither inert nor genuine-Django.

    A pending ``_deferred_filter``'s ``args`` / ``kwargs`` are baked by ``add_q`` ->
    ``build_filter``, which dispatches ``resolve_expression(self=query)`` on any value
    that is an expression -- a consumer expression could there erase the visibility
    predicate and return a genuine-looking ``Value`` that the post-bake walk cannot
    detect (``docs/feedback.md`` Finding 2). So every value is proven BEFORE the bake:

    - an inert query parameter, a nested ``Q`` (its children recurse), or a plain
      container is safe;
    - an object Django will treat as an EXPRESSION (its type defines
      ``resolve_expression``) must be a genuine, unshadowed Django expression graph;
    - a model instance WITHOUT a class- OR instance-level ``resolve_expression`` is the
      legitimate reverse-relation value (``RelatedManager.core_filters`` stores the
      instance); Django extracts its pk to a bound parameter and never hands it the
      query, so it cannot strip the predicate. ``build_filter`` decides whether to
      dispatch via ``hasattr(value, "resolve_expression")`` -- which finds an
      INSTANCE-level attribute too -- so a model instance carrying ``resolve_expression``
      in its own ``__dict__`` would still be dispatched and fails closed
      (``docs/feedback.md`` P1 inert-subclass, model-instance half);
    - anything else fails closed.
    """
    if _is_inert_value(value):
        return None
    value_type = type(value)
    if value_type is models.Q:
        # ``Q`` trees and plain containers memoize by id like the expression walk:
        # a self-referential ``Q`` / list / dict would otherwise recurse without
        # bound and escape as a raw ``RecursionError`` past the typed contract.
        value_id = id(value)
        if value_id in seen:
            return None
        seen.add(value_id)
        for child in value.children:
            if type(child) is models.Q:
                child_defect = _deferred_value_defect(child, seen, label)
            elif type(child) is tuple and len(child) == 2 and type(child[0]) is str:
                child_defect = _deferred_value_defect(child[1], seen, label)
            else:
                return ("untrusted", f"{label} Q child is a {type(child).__name__}")
            if child_defect is not None:
                return child_defect
        return None
    if value_type in (
        list,
        tuple,
        set,
        frozenset,
    ):
        value_id = id(value)
        if value_id in seen:
            return None
        seen.add(value_id)
        for item in value:
            item_defect = _deferred_value_defect(item, seen, label)
            if item_defect is not None:
                return item_defect
        return None
    if value_type is dict:
        value_id = id(value)
        if value_id in seen:
            return None
        seen.add(value_id)
        for key, item in value.items():
            if type(key) is not str:
                return ("untrusted", f"{label} mapping key is a {type(key).__name__}")
            item_defect = _deferred_value_defect(item, seen, label)
            if item_defect is not None:
                return item_defect
        return None
    if getattr(value_type, "resolve_expression", None) is not None:
        return _expr_graph_defect(value, seen, label)
    if isinstance(value, models.Model):
        # A class-level ``resolve_expression`` was handled above; an INSTANCE-level one
        # (in the model instance's own ``__dict__``) is still found by ``build_filter``'s
        # ``hasattr`` and dispatched, so reject it. Read ``__dict__`` directly to detect
        # the shadow without triggering it.
        if "resolve_expression" in object.__getattribute__(value, "__dict__"):
            return ("untrusted", f"{label} model instance shadows resolve_expression")
        return None
    return ("untrusted", f"{label} is a {value_type.__name__}")


def _bake_deferred_filter_or_defect(
    rebuilt_query: Any,
    deferred: Any,
    cls_name: str,
) -> tuple[str, str] | None:
    """Bake a validated ``_deferred_filter`` onto the DETACHED clone, or return a defect.

    ``deferred`` is the ``(negate, args, kwargs)`` tuple Django's
    ``RelatedManager._apply_rel_filters`` leaves on ``instance.rel.all()`` (baked into
    ``_query`` only on first ``.query`` access). Resolved WITHOUT Django's
    ``QuerySet.query`` getter -- whose ``_filter_or_exclude_inplace`` / ``add_q`` are
    instance-shadowable and would dispatch consumer code mid-seal -- and WITHOUT
    mutating the candidate: the predicate is added to ``rebuilt_query`` (a
    framework-owned clone) through the UNBOUND ``sql.Query.add_q``. Every argument is
    proven inert / genuine-Django FIRST (``_deferred_value_defect``) so ``add_q``'s
    ``resolve_expression`` dispatch (``docs/feedback.md`` Finding 2) only ever runs
    genuine Django code. A malformed shape Django never produces (a non-3-tuple, a
    non-dict / non-tuple args, a prohibited ``_connector`` / ``_negated`` kwarg, a bad
    field) fails closed as a typed ``untrusted`` defect, never a raw exception.
    """
    # Exact-shape gate BEFORE the unpack: tuple unpacking dispatches ``__iter__``,
    # so an arbitrary object planted in the slot must be rejected without iteration.
    if type(deferred) is not tuple or len(deferred) != 3:
        return ("untrusted", f"{cls_name} deferred filter is malformed")
    negate, args, kwargs = deferred
    if type(kwargs) is not dict:
        return ("untrusted", f"{cls_name} deferred filter kwargs is a {type(kwargs).__name__}")
    if type(args) not in (tuple, list):
        return ("untrusted", f"{cls_name} deferred filter args is a {type(args).__name__}")
    if PROHIBITED_FILTER_KWARGS.intersection(kwargs):
        return ("untrusted", f"{cls_name} deferred filter carries prohibited kwargs")
    seen: set[int] = set()
    for value in args:
        arg_defect = _deferred_value_defect(value, seen, f"{cls_name} deferred filter arg")
        if arg_defect is not None:
            return arg_defect
    for key, value in kwargs.items():
        if type(key) is not str:
            return ("untrusted", f"{cls_name} deferred filter kwarg key is a {type(key).__name__}")
        kwarg_defect = _deferred_value_defect(value, seen, f"{cls_name} deferred filter {key!r}")
        if kwarg_defect is not None:
            return kwarg_defect
    try:
        predicate = models.Q(*args, **kwargs)
        sql.Query.add_q(rebuilt_query, ~predicate if negate else predicate)
    except Exception:
        return ("untrusted", f"{cls_name} carries a deferred filter that cannot be resolved")
    return None


def _queryset_state_defect(state: dict, cls_name: str) -> tuple[str, str] | None:
    """Return a defect if a RETAINED ``QuerySet`` state field is not its exact shape.

    Beyond the query graph, the seal carries a handful of ``QuerySet.__dict__`` fields
    onto the rebuilt queryset (``_db`` routing, ``_hints``, ``_fields``,
    ``_sticky_filter``, ``_for_write``). Each is later subjected to truthiness, an
    equality / ``str`` comparison, or a ``dict`` copy; a consumer object overriding
    ``__bool__`` / ``__eq__`` / ``__str__`` / ``__iter__`` there would dispatch mid-seal
    even though the field was read from ``__dict__`` without dispatch
    (``docs/feedback.md`` P2 retained-state). So each is pinned to the EXACT shape Django
    stores before it is used:

    - ``_db``: ``None`` or an exact ``str`` alias;
    - ``_hints``: ``None`` or an exact ``dict`` with exact-``str`` keys;
    - ``_fields``: ``None`` or an exact ``tuple`` / ``list`` of exact ``str`` names;
    - ``_sticky_filter`` / ``_for_write``: ``None`` or an exact ``bool``.
    """
    db = state.get("_db")
    if db is not None and type(db) is not str:
        return ("untrusted", f"{cls_name}._db is a {type(db).__name__}")
    hints = state.get("_hints")
    if hints is not None:
        if type(hints) is not dict:
            return ("untrusted", f"{cls_name}._hints is a {type(hints).__name__}")
        for key in hints:
            if type(key) is not str:
                return ("untrusted", f"{cls_name}._hints has a non-string key")
    fields = state.get("_fields")
    if fields is not None:
        if type(fields) not in (tuple, list):
            return ("untrusted", f"{cls_name}._fields is a {type(fields).__name__}")
        for name in fields:
            if type(name) is not str:
                return ("untrusted", f"{cls_name}._fields carries a {type(name).__name__}")
    for attr in ("_sticky_filter", "_for_write"):
        flag = state.get(attr)
        if flag is not None and type(flag) is not bool:
            return ("untrusted", f"{cls_name}.{attr} is a {type(flag).__name__}")
    return None


def _seal_or_defect(
    candidate: Any,
    model: type[models.Model],
    required_alias: str | None,
    *,
    require_model_rows: bool = True,
    allow_sliced: bool = False,
    require_shared_alias: bool = False,
) -> tuple[models.QuerySet | None, tuple[str, str] | None]:
    """Rebuild a framework-owned plain ``QuerySet`` from ``candidate``'s validated state.

    The single sealing primitive both boundary sites run. Returns
    ``(sealed_queryset, None)`` on success, or ``(None, (code, detail))`` on the
    first defect. Codes run ``type`` -> ``table`` -> ``untrusted`` -> ``sliced``
    -> ``projection`` -> ``alias`` (the one canonical ordering both sites
    share), except that the outer exact-``sql.Query`` check (``untrusted``) runs
    BEFORE the combinator table walk: the walk reads query attributes through
    normal attribute access, so only a proven-genuine ``sql.Query`` may be
    walked.

    Every read of ``candidate`` state comes from its instance ``__dict__`` (via
    ``object.__getattribute__``), never through attribute access, so a custom
    ``__getattribute__``, an instance-shadowed callable, or a redefined ``query``
    / ``_query`` descriptor cannot run code or return a lie during extraction.
    The extracted state is what BOTH the validation checks and the rebuilt seal
    consume, so validation and execution provably cannot diverge.

    Defects:

    - ``type`` -- not a ``QuerySet`` at all.
    - ``table`` -- a contributing table (public ``QuerySet.model``, SQL-bearing
      ``Query.model``, the baked base table in ``Query.alias_map``, or any
      ``combined_queries`` branch) is not the registered type's concrete table.
    - ``untrusted`` -- the state cannot be faithfully rebuilt into a trusted
      execution queryset: the ``_query`` is not exactly ``django.db.models.sql``
      ``.Query`` (a foreign ``Query`` subclass), a ``combined_queries`` branch is
      a foreign ``Query`` subclass (the outer exact-type check never reaches the
      branches, yet ``sql.Query.clone`` preserves them), the query instance
      shadows a callable ``sql.Query`` method in its ``__dict__`` (``chain`` /
      ``clone`` / any -- ``sql.Query.clone`` shallow-copies the source
      ``__dict__``, so the shadow would dispatch on the first post-seal transform),
      a container ``sql.Query.clone`` copies (``alias_map`` / ``annotations`` /
      ``used_aliases`` / ...) is not an exact builtin (a ``dict`` / ``set`` subclass
      whose ``.copy()`` would dispatch mid-clone, or a non-string mapping key), an
      embedded AST node ``sql.Query.clone`` clones or the compiler later executes is
      not a trusted Django implementation, proven by a COMPLETE recursive
      identity-memoized walk of every compiler-reachable node -- the ``where`` /
      ``having`` trees AND their leaf operands, ``annotations`` (incl. nested ``Func``
      / ``Case`` operands and inner ``Subquery`` graphs), ``order_by`` / ``group_by``
      / ``distinct`` / ``select`` sequences, ``alias_map`` joins, ``select_related``
      -- where each node must be an EXACT genuine Django type (proven by object
      identity against ``sys.modules``, never the spoofable ``__module__``) that is
      unshadowed (a consumer ``WhereNode`` subclass, a consumer expression anywhere in
      the graph, a consumer join, an exact Django node with a shadowed ``as_sql``, or
      a foreign ``select_related`` all fail closed -- consumer-defined expressions /
      lookups are NOT supported across the visibility boundary), the
      ``_iterable_class`` is not one of Django's own row iterables (a synthetic-row
      iterable), a SUBCLASS instance carries an unresolved ``_deferred_filter`` -- a
      predicate not yet baked into the query (an EXACT plain ``QuerySet`` carrying
      one, as ``RelatedManager._apply_rel_filters`` leaves on ``instance.rel.all()``,
      is baked onto the DETACHED CLONE through the UNBOUND ``sql.Query.add_q`` after
      every argument is proven inert / genuine-Django, never Django's
      ``QuerySet.query`` getter -- whose ``_filter_or_exclude_inplace`` / ``add_q``
      are instance-shadowable and whose ``resolve_expression`` dispatch would run a
      consumer expression mid-bake; the candidate is never mutated; a MALFORMED
      deferred filter Django never produces fails closed as a typed defect, not a raw
      exception) -- or a
      ``Prefetch`` in ``_prefetch_related_lookups`` carries an inner queryset that
      cannot itself be sealed, a non-exact-``str`` lookup, or a consumer
      ``Prefetch`` subclass (rebuilt as an exact ``Prefetch`` so no
      ``get_current_querysets`` override survives). This REPLACES the old
      class-level method inventory: ``untrusted`` now means "cannot be sealed",
      not "overrides a listed method".
    - ``sliced`` -- only when ``require_model_rows`` (every read surface): the
      query is sliced (a ``LIMIT`` / ``OFFSET`` was taken). Django forbids
      reordering or refiltering a sliced query, so the next framework transform
      (a Relay ``.filter(pk=...)``, a connection ordering) would raise a raw
      ``TypeError`` outside the typed defect contract. The cascade
      (``require_model_rows=False``) keeps its own slice rejection in
      ``permissions.py::_validated_target_subquery``. ``allow_sliced`` (private,
      default ``False``) suppresses ONLY this slice rejection while leaving
      ``require_model_rows`` in force: it is set solely for a ``Prefetch`` child
      (a legal sliced top-N-per-parent prefetch queryset), which nothing
      refilters, so the rejection's premise does not hold one edge down.
    - ``projection`` -- only when ``require_model_rows`` (every surface except
      the cascade): the row iterable is not ``ModelIterable`` (a ``.values()`` /
      ``.values_list()`` projection whose rows are not model instances). The
      cascade passes ``require_model_rows=False`` because it re-projects the
      sealed queryset to the edge's target column and never iterates it.
    - ``alias`` -- a value explicitly routed off ``required_alias``. For a
      top-level source an UNROUTED value (``_db is None``) is never an alias defect;
      the seal pins it via ``using=`` at construction. For a prefetch child
      (``require_shared_alias``), the child's explicit ``_db`` must EQUAL the outer
      effective alias, including when that alias is ``None`` -- an unrouted parent
      forces an unrouted child, so one resolution never spans two connections.

    An instance-shadowed clone / evaluation method (the review's ``.all()``,
    ``Query.chain``, ``.filter()``, ``_values``, ``.first()``, ``.__aiter__()``
    probes) is neutralized WITHOUT rejection: the seal never dispatches through the
    consumer object, it rebuilds a plain queryset from the extracted query and clones
    that query through the unbound ``sql.Query.clone``. Clone-safety is not assumed
    from the outer exact-type alone: ``sql.Query.clone`` dispatches ``where.clone()``,
    container ``.copy()`` methods, and (at compile) ``as_sql`` on the graph, so the
    seal first proves via ``_combined_query_table_defect`` that EVERY compiler-reachable
    node is a genuine, unshadowed Django implementation and every cloned container an
    exact builtin -- only then does the clone provably dispatch trusted code alone.
    """
    if not isinstance(candidate, models.QuerySet):
        return None, ("type", type(candidate).__name__)
    state = object.__getattribute__(candidate, "__dict__")
    query = state.get("_query")
    qmodel = state.get("model")
    db = state.get("_db")
    iterable = state.get("_iterable_class")
    concrete = model._meta.concrete_model
    cls_name = type(candidate).__name__
    if _concrete_or_none(qmodel) is not concrete:
        return None, ("table", getattr(qmodel, "__name__", type(qmodel).__name__))
    # The outer exact-type check must precede the table walk AND the deferred-filter
    # resolution below: the walk reads ``query.model`` / ``query.alias_map`` /
    # ``query.combined_queries`` through normal attribute access, which on a foreign
    # ``Query`` SUBCLASS could dispatch a consumer property during validation. Only a
    # proven-genuine ``sql.Query`` is walked (the walk itself type-checks each branch
    # before recursing into it, extending the same discipline down the combinator tree).
    if type(query) is not sql.Query:
        return None, ("untrusted", f"{cls_name}.query is {type(query).__name__}")
    # Pin every retained ``QuerySet`` state field (``_db`` / ``_hints`` / ``_fields`` /
    # ``_sticky_filter`` / ``_for_write``) to its exact shape BEFORE any truthiness /
    # comparison / copy runs on it, so a consumer ``__bool__`` / ``__eq__`` / ``__iter__``
    # cannot dispatch mid-seal (``docs/feedback.md`` P2 retained-state).
    state_defect = _queryset_state_defect(state, cls_name)
    if state_defect is not None:
        return None, state_defect
    # Validate the candidate's ENTIRE query graph BEFORE cloning it. sql.Query.clone is
    # not a no-dispatch boundary: its body calls bound methods on the source's own
    # sub-objects -- ``self.where.clone()``, ``alias_refcount.copy()`` /
    # ``annotations.copy()`` / ... on the containers, and (at compile time) ``as_sql``
    # on every embedded node -- so a consumer WhereNode / expression / container
    # SUBCLASS, or an instance-dict method shadow on an EXACT Django node, would run
    # mid-clone and strip the visibility predicate (an adversarial review reproduced
    # this against an exact WhereNode whose shadowed ``clone()`` fired and left the
    # sealed SQL with no WHERE). ``_combined_query_table_defect`` now proves every
    # compiler-reachable node is a genuine, unshadowed Django implementation and every
    # cloned container an exact builtin, so the clone below dispatches only trusted code.
    pre_clone_defect = _combined_query_table_defect(query, concrete)
    if pre_clone_defect is not None:
        return None, pre_clone_defect
    # Clone ONCE, off the proven-safe candidate, into a framework-owned detached query.
    # Every subsequent step (deferred-filter baking) mutates only this clone, never the
    # candidate -- the seal is observationally immutable, so a concurrent caller reusing
    # the same source queryset never observes a half-baked predicate, a cleared
    # ``_deferred_filter``, or partial state left after an exception mid-bake.
    rebuilt_query = sql.Query.clone(query)
    # A pending ``_deferred_filter`` -- the ``(negate, args, kwargs)`` tuple Django's
    # ``RelatedManager._apply_rel_filters`` leaves on ``instance.rel.all()`` (baked into
    # ``_query`` only on first ``.query`` access) -- is baked onto the CLONE for an EXACT
    # plain ``QuerySet``. A SUBCLASS leaving a predicate pending is not that
    # reverse-relation artifact and cannot be safely resolved, so it fails closed.
    # ``is not None`` -- never truthiness: Django only ever stores ``None`` or the
    # 3-tuple here, and ``if deferred:`` would dispatch a consumer ``__bool__`` on an
    # arbitrary object planted in the slot (the P2 retained-state vector), letting a
    # falsy hostile value silently skip the bake. Any non-``None`` value now routes
    # through the bake path, whose exact-shape checks fail a malformed one closed.
    deferred = state.get("_deferred_filter")
    if deferred is not None:
        if type(candidate) is not models.QuerySet:
            return None, ("untrusted", f"{cls_name} carries an unresolved deferred filter")
        bake_defect = _bake_deferred_filter_or_defect(rebuilt_query, deferred, cls_name)
        if bake_defect is not None:
            return None, bake_defect
        # Re-prove the detached clone after baking: the predicate was added by unbound
        # Django machinery over arguments PRE-validated inert / genuine-Django (so no
        # consumer ``resolve_expression`` ran mid-bake -- the Finding-2 vector), and this
        # walk re-proves the whole graph is still genuine and confined to concrete's table.
        post_bake_defect = _combined_query_table_defect(rebuilt_query, concrete)
        if post_bake_defect is not None:  # pragma: no cover - defense in depth
            # Genuinely unreachable through any validated input: every deferred-filter
            # argument is proven inert or genuine-unshadowed Django BEFORE the bake, and
            # ``sql.Query.add_q`` is Django's own machinery -- it can only assemble
            # genuine Django ``WhereNode`` / lookup / expression nodes over the base
            # concrete table, never a foreign type, a shadowed method, a non-exact
            # container, a foreign base table, or a combined branch. The re-prove is
            # kept as a belt-and-suspenders re-validation of the MUTATED clone (a
            # security-boundary invariant), but no argument the pre-bake proof admits can
            # drive this branch, so it is marked unreachable rather than surfaced with a
            # synthetic test that would have to bypass the pre-bake proof.
            return None, post_bake_defect
    # Identity membership, never ``in`` on the frozenset: set membership would hash the
    # candidate iterable, dispatching a consumer metaclass ``__hash__`` / ``__eq__``
    # (``docs/feedback.md`` P2 retained-state). ``is`` compares object identity only.
    if not any(iterable is cls for cls in _DJANGO_ITERABLE_CLASSES):
        detail = getattr(iterable, "__name__", type(iterable).__name__)
        return None, ("untrusted", f"{cls_name}._iterable_class is {detail}")
    # The outer effective alias is what this seal pins the queryset onto (a required
    # alias, else the source's own explicit ``_db``); prefetch children are sealed
    # against it with ``require_shared_alias=True`` so neither a pinned parent nor an
    # UNROUTED parent (effective alias ``None``) can hold an explicitly cross-routed
    # child -- one GraphQL resolution never spans two database connections.
    effective_alias = required_alias if required_alias is not None else db
    sealed_prefetch, prefetch_defect = _sealed_prefetch_related_lookups(
        state.get("_prefetch_related_lookups"),
        cls_name,
        effective_alias,
    )
    if prefetch_defect is not None:
        return None, prefetch_defect
    if require_model_rows and not allow_sliced and rebuilt_query.is_sliced:
        return None, ("sliced", f"rows {rebuilt_query.low_mark}:{rebuilt_query.high_mark}")
    if require_model_rows and iterable is not ModelIterable:
        return None, ("projection", getattr(iterable, "__name__", type(iterable).__name__))
    if require_shared_alias:
        # A prefetch child: its explicit ``_db`` must EQUAL the outer effective alias,
        # INCLUDING when that alias is ``None`` (an unrouted parent forces an unrouted
        # child). ``required_alias`` here IS the outer effective alias.
        if db is not None and db != required_alias:
            return None, ("alias", str(db))
    elif required_alias is not None and db is not None and db != required_alias:
        return None, ("alias", str(db))
    using = required_alias if required_alias is not None else db
    # ``_hints`` is proven ``None`` or an exact ``dict`` by ``_queryset_state_defect``,
    # so ``dict(...)`` copies it without dispatching a consumer ``__iter__`` / ``keys``.
    # A fresh dict, never the candidate's own ``_hints`` object: sharing it would leave
    # the sealed queryset holding a mutable dict the untrusted object can still write to
    # (a routing-control surface when a custom router consults hints on an unrouted read).
    hints = state.get("_hints")
    sealed = models.QuerySet(
        model=qmodel,
        query=rebuilt_query,
        using=using,
        hints=dict(hints) if hints is not None else {},
    )
    # Reproduce exactly what ``QuerySet._clone`` copies forward -- from state read
    # without dispatch and proven exact-shape by ``_queryset_state_defect`` -- MINUS
    # ``_known_related_objects`` (an optional related-object cache we deliberately drop:
    # a fresh fetch is always correct, whereas copying an untrusted cache could pre-seed
    # synthetic related instances that bypass the related type's own visibility hook).
    sealed._iterable_class = iterable
    sealed._fields = state.get("_fields")
    sealed._prefetch_related_lookups = sealed_prefetch
    sealed._sticky_filter = state.get("_sticky_filter") is True
    sealed._for_write = state.get("_for_write") is True
    return sealed, None


def _coerced_manager_queryset(manager: models.Manager) -> models.QuerySet:
    """Coerce a ``Manager`` to its ``QuerySet``, preserving its explicit alias or failing closed.

    ``Manager.all()`` is consumer-overridable. A custom Manager can degrade it
    into a plain list / generator (which would otherwise be mistaken for the
    deliberate plain-iterable bypass and skip the visibility hook) or silently
    change the database it routes to (an explicitly ``.using("chosen")`` manager
    whose ``.all()`` returns rows on ``"elsewhere"``, or an unrouted manager that
    self-routes before the boundary's required-alias step runs). Both are
    cross-database / bypass leaks, so the coercion result must be a real
    ``QuerySet`` whose ``_db`` EXACTLY preserves the manager's explicit routing
    (an unrouted manager must stay unrouted until the required-alias resolution
    pins it). The returned queryset still flows through the full source /
    result validation (concrete table, actual base table, trust, alias); this
    helper only closes the Manager-coercion-specific holes.
    """
    explicit = getattr(manager, "_db", None)
    queryset = manager.all()
    if not isinstance(queryset, models.QuerySet):
        raise ConfigurationError(
            f"A {type(manager).__name__}.all() coercion must produce a QuerySet, but "
            f"returned {type(queryset).__name__}; a Manager that degrades into a list "
            f"or other non-queryset cannot enter the visibility boundary and must not "
            f"be treated as the deliberate plain-iterable bypass.",
        )
    if queryset._db != explicit:
        raise ConfigurationError(
            f"A {type(manager).__name__} pinned to alias {explicit!r} produced a "
            f"queryset routed to {queryset._db!r} on .all(); a Manager coercion must "
            f"preserve the manager's explicit routing exactly (an unrouted manager "
            f"must stay unrouted until the resolution's required alias pins it), so a "
            f"visibility source or hook cannot silently change databases.",
        )
    return queryset


def _visibility_result_error(
    type_cls: type,
    model: type[models.Model],
    required_alias: str | None,
    defect: tuple[str, str],
    render_error: Any,
) -> ConfigurationError:
    """Build the fail-closed error for a defective ``get_queryset`` result.

    ``render_error`` is the caller-supplied error-rendering seam: a
    ``(code, detail) -> str`` callable whose message replaces the default
    wording wholesale. The cascade passes one so its path-rich per-edge
    prose (``"... for the cascade subquery on Model.field ..."``) survives
    the checks moving into this shared boundary; surfaces without bespoke
    prose take the defaults below.
    """
    code, detail = defect
    if render_error is not None:
        return ConfigurationError(render_error(code, detail))
    if code == "type":
        return ConfigurationError(
            f"{type_cls.__name__}.get_queryset must return a QuerySet or Manager of "
            f"{model.__name__} rows; got {detail}. A list / generator / iterable has no "
            f"lazy query for the surface to compose into, and None discards the "
            f"visibility contract entirely.",
        )
    if code == "table":
        return ConfigurationError(
            f"{type_cls.__name__}.get_queryset returned a {detail} queryset; the "
            f"visibility contract composes over {model.__name__}'s concrete table "
            f"(proxy siblings are compatible, MTI children and unrelated models are not).",
        )
    if code == "untrusted":
        return ConfigurationError(
            f"{type_cls.__name__}.get_queryset returned a queryset that cannot be sealed "
            f"into a framework-owned execution queryset ({detail}); the visibility "
            f"boundary rebuilds a plain QuerySet from the validated query state, and a "
            f"foreign Query class, a foreign row iterable, or an unresolved deferred "
            f"filter cannot be faithfully rebuilt. Return a queryset backed by a plain "
            f"django.db.models.sql.Query over model or .values() rows.",
        )
    if code == "sliced":
        return ConfigurationError(
            f"{type_cls.__name__}.get_queryset returned a sliced queryset ({detail}); "
            f"the surface composes further filters and ordering onto the hook result, "
            f"and Django forbids refiltering or reordering a sliced query, so the next "
            f"transform would raise a raw TypeError outside the visibility contract. "
            f"Return the unsliced queryset and let the surface paginate.",
        )
    if code == "projection":
        return ConfigurationError(
            f"{type_cls.__name__}.get_queryset returned a {detail} projection; the "
            f"visibility contract composes over {model.__name__} model rows, not a "
            f".values() / .values_list() (or custom-iterable) projection whose rows "
            f"are not {model.__name__} instances. Return a queryset of model rows.",
        )
    # ``code == "alias"`` -- the only remaining defect the shared checker emits;
    # an unhandled future code would fall through silently, so this last branch
    # is unconditional.
    return ConfigurationError(
        f"{type_cls.__name__}.get_queryset returned a queryset routed to alias "
        f"{detail!r}, but this resolution is pinned to alias {required_alias!r}; "
        f"a visibility hook cannot re-route a pinned resolution. Remove the "
        f".using(...) call.",
    )


def _prepared_visibility_source(
    type_cls: type,
    queryset: Any,
    *,
    require_model_rows: bool = True,
    allow_sliced: bool = False,
) -> tuple[models.QuerySet, str | None]:
    """Validate and SEAL the source queryset before the visibility hook runs.

    Returns ``(sealed_queryset, required_alias)``. The source is sealed through
    ``_seal_or_defect`` before the hook runs - it must be a real ``QuerySet``
    over the registered type's concrete table, sealable (a plain ``sql.Query``, a
    Django row iterable, no unresolved deferred filter), and model rows (unless
    ``require_model_rows`` is off for the cascade). ``allow_sliced`` (default
    ``False``) forwards to the seal to suppress ONLY the slice rejection, for the
    optimizer walker's nested-connection path whose own gate
    (``nested_fetch.py::unwindowable_child_queryset_reason``) classifies a sliced
    child and degrades to the fully-unplanned per-parent fallback WITHOUT
    recomposing filters / ordering -- so the "next transform would recompose"
    premise the rejection guards against does not hold there
    (``docs/feedback2.md`` P0-3 degrade-to-unplanned). The sealed object is a fresh
    framework-owned plain ``QuerySet`` rebuilt from the source's query state, so
    the hook receives a trusted queryset regardless of what the caller passed;
    an already-evaluated source seals to a fresh, unevaluated queryset (the seal
    never copies ``_result_cache``), so cached rows never reach the hook. The
    required alias is then resolved in priority order:

    1. An active write pipeline's alias - the sealed source is pinned through
       ``pin_write_queryset`` (a genuine ``.using()`` on the trusted object),
       which fail-closes an explicitly divergent source alias.
    2. The sealed source's own explicit ``_db`` (a caller that routed with
       ``.using(...)`` keeps that routing through the hook).
    3. ``None`` - no required alias; an unpinned read hook keeps its
       documented ability to choose ``.using(alias)`` itself.

    Resolver-source ``Manager`` coercion stays in ``normalize_query_source``;
    framework-created seeds are querysets by construction. Preparation composes
    lazy query state only; it executes zero SQL.
    """
    model = model_for(type_cls)
    queryset, defect = _seal_or_defect(
        queryset,
        model,
        None,
        require_model_rows=require_model_rows,
        allow_sliced=allow_sliced,
    )
    if defect is not None:
        code, detail = defect
        if code == "type":
            raise ConfigurationError(
                f"apply_type_visibility requires a QuerySet of {model.__name__} rows "
                f"for {type_cls.__name__}; got {detail}. Coerce a Manager with .all(); "
                f"a list has no lazy query for the hook to narrow.",
            )
        if code == "untrusted":
            raise ConfigurationError(
                f"apply_type_visibility for {type_cls.__name__} got a source queryset "
                f"that cannot be sealed into a framework-owned execution queryset "
                f"({detail}); the boundary rebuilds a plain QuerySet from the validated "
                f"query state, and a foreign Query class, a foreign row iterable, or an "
                f"unresolved deferred filter cannot be faithfully rebuilt. Pass a "
                f"queryset backed by a plain django.db.models.sql.Query.",
            )
        if code == "sliced":
            raise ConfigurationError(
                f"apply_type_visibility for {type_cls.__name__} got a sliced source "
                f"queryset ({detail}); the visibility hook and the surface compose "
                f"further filters and ordering onto the source, and Django forbids "
                f"refiltering or reordering a sliced query. Pass the unsliced queryset "
                f"and let the surface paginate.",
            )
        if code == "projection":
            raise ConfigurationError(
                f"apply_type_visibility for {type_cls.__name__} got a {detail} projection "
                f"source; the visibility contract composes over {model.__name__} model "
                f"rows, not a .values() / .values_list() (or custom-iterable) projection.",
            )
        # ``code == "table"`` -- the only other defect reachable with no
        # required alias on a model-row source.
        raise ConfigurationError(
            f"apply_type_visibility for {type_cls.__name__} requires a QuerySet over "
            f"{model.__name__}'s concrete table; got a {detail} queryset (proxy "
            f"siblings are compatible, MTI children and unrelated models are not).",
        )
    pipeline = current_write_pipeline()
    if pipeline is not None:
        queryset = pin_write_queryset(
            queryset,
            pipeline.alias,
            owner=f"The {type_cls.__name__} visibility source",
        )
        required_alias = pipeline.alias
    else:
        required_alias = queryset._db
    return queryset, required_alias


def _normalized_visibility_result(
    type_cls: type,
    result: Any,
    required_alias: str | None,
    render_error: Any = None,
    *,
    require_model_rows: bool = True,
    allow_sliced: bool = False,
) -> models.QuerySet:
    """Normalize a ``get_queryset`` hook result into a composable, correctly-routed queryset.

    The shared result contract both colored visibility runners apply (the sealed
    boundary): a ``Manager`` is coerced exactly once through
    ``_coerced_manager_queryset`` (which preserves the manager's explicit
    routing and fails a degrade-to-non-queryset closed); the coerced value is
    then SEALED through ``_seal_or_defect``, so anything that is not a sealable
    ``QuerySet`` of the registered type's model rows (``None``, lists,
    generators, async generators, custom iterables, unrelated / MTI-child
    models, cross-model unions, base-table spoofs, foreign Query classes,
    ``.values()`` projections on non-cascade surfaces) fails closed. The return
    value is a fresh framework-owned plain ``QuerySet`` rebuilt from the hook
    result's validated query state - never the consumer object - so an
    instance-shadowed ``.all()`` / ``.filter()`` / ``.first()`` / ``.__aiter__()``
    or a replaced ``Query.chain`` cannot erase the predicate or synthesize rows
    after this point.

    Alias handling is done at construction: the seal passes
    ``using=required_alias`` when an alias is required (an unpinned result is
    pinned onto it, an explicitly matching one is preserved, an explicitly
    divergent one fails closed with the ``alias`` defect); with no required
    alias the hook's own ``_db`` is preserved. There is no post-seal ``.using()``
    repin or ``.all()`` refresh - the sealed queryset is fresh and correctly
    routed by construction. Normalization composes lazy query state only -
    filters, annotations, ordering, and values projection pass through unchanged
    (but subclass identity is deliberately dropped) - and executes zero SQL.
    """
    model = model_for(type_cls)
    if isinstance(result, models.Manager):
        result = _coerced_manager_queryset(result)
    sealed, defect = _seal_or_defect(
        result,
        model,
        required_alias,
        require_model_rows=require_model_rows,
        allow_sliced=allow_sliced,
    )
    if defect is not None:
        raise _visibility_result_error(type_cls, model, required_alias, defect, render_error)
    return sealed


def apply_type_visibility_sync(
    type_cls: type,
    queryset: models.QuerySet,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
    *,
    render_error: Any = None,
    require_model_rows: bool = True,
    allow_sliced: bool = False,
) -> models.QuerySet:
    """Run ``type_cls.get_queryset`` in a sync context; reject async hooks loudly.

    Decision 9 makes a consumer's ``DjangoType.get_queryset`` allowed to
    be sync or async, but a sync resolver context cannot await an async
    hook safely (event-loop edge cases dominate the bridge). On the sync
    path we therefore close the unawaited coroutine to silence the
    "coroutine was never awaited" warning and raise a named
    ``SyncMisuseError`` (a ``ConfigurationError`` subclass that also
    inherits ``RuntimeError``) that points the consumer at the correct
    recourse for the surface that called in.

    The source is prepared and the result normalized through the shared sealed
    boundary (``_prepared_visibility_source`` / ``_normalized_visibility_result``):
    the source and the hook result are each SEALED into a fresh framework-owned
    plain ``QuerySet`` rebuilt from validated query state (shape, concrete +
    actual-base table, sealability, model-row, alias), with required-alias
    resolution (write pipeline > explicit source ``.using`` > none), Manager
    coercion with alias preservation, and fail-closed rejection of every
    non-sealable shape. ``SyncMisuseError`` stays reserved for this sync
    boundary; every other defect is a plain ``ConfigurationError``.

    ``async_recourse`` is the surface-specific guidance appended to the
    error. It defaults to the Relay node-defaults wording; callers whose
    recourse differs pass their own (the cascade, for instance, has no
    async-native walk -- its twin wraps this same sync walk -- so it tells
    the consumer to make the target hook sync or scope ``fields=`` rather
    than reach for an async resolver that cannot help, feedback M1).
    ``render_error`` is the result-normalization error seam
    (``_visibility_result_error``): the cascade supplies its path-rich
    per-edge prose; other surfaces take the shared defaults.
    ``require_model_rows`` defaults ``True`` (a read surface's hook must return
    model rows); the cascade passes ``False`` because it deliberately accepts a
    ``.values()`` / ``.values_list()`` return and re-projects it to the edge's
    target column, and never iterates the target's rows.
    ``allow_sliced`` defaults ``False`` (every recomposing read surface -- Relay
    node defaults, connection root, list field, cascade -- rejects a sliced hook
    result, because Django forbids reordering / refiltering a sliced query). Only
    the optimizer walker's nested-connection plan path passes ``True``: its own
    gate (``nested_fetch.py::unwindowable_child_queryset_reason``) detects the
    sliced child and degrades the nested connection to the fully-unplanned
    per-parent fallback WITHOUT recomposing, so the rejection's "next transform
    would recompose" premise does not hold one edge down (``docs/feedback2.md``
    P0-3 degrade-to-unplanned; mirrors the prefetch-child ``allow_sliced``).
    """
    queryset, required_alias = _prepared_visibility_source(
        type_cls,
        queryset,
        require_model_rows=require_model_rows,
        allow_sliced=allow_sliced,
    )
    result = type_cls.get_queryset(queryset, info)
    result = reject_async_in_sync_context(
        result,
        owner=type_cls.__name__,
        method="get_queryset",
        context="resolver",
        recourse=async_recourse,
    )
    # No identity fast path: ``result is queryset`` proves object identity, not
    # immutability. A hook that held the sealed source can mutate ``_result_cache``
    # / ``_query`` / ``model`` / ``_db`` and return the SAME object, so the result
    # is ALWAYS re-sealed -- the second seal is the point that drops any injected
    # result cache and re-validates post-hook state (``docs/feedback.md`` P1-2).
    return _normalized_visibility_result(
        type_cls,
        result,
        required_alias,
        render_error,
        require_model_rows=require_model_rows,
        allow_sliced=allow_sliced,
    )


def visibility_scoped_related_queryset(
    related_type: type,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> models.QuerySet:
    """Return a related type's base queryset scoped by its ``get_queryset`` visibility hook.

    The one-line composition of the two primitives every relation-visibility check
    shares - ``apply_type_visibility_sync(related_type, initial_queryset(
    related_type), info, recourse)``. Single-sourced so the model relation decode
    (``mutations/resolvers.py``) and the form relation decode
    (``forms/resolvers.py``) provably apply the SAME related-type ``get_queryset``
    (the cross-flavor security invariant spec-038 claims), rather than re-spelling
    the composition at each site. ``async_recourse`` stays a parameter: the model
    and form paths pass their own surface-specific wording.
    """
    return apply_type_visibility_sync(
        related_type,
        initial_queryset(related_type),
        info,
        async_recourse,
    )


def related_visibility_queryset(
    related_model: type,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> models.QuerySet | None:
    """Return the related model's visibility-scoped queryset, or ``None`` when it has no primary.

    The ``registry.get(related_model)`` resolve + the "scope through the primary
    ``DjangoType.get_queryset`` visibility hook, else no contract" branch that four
    relation surfaces open with (``visible_related_object`` /
    ``visible_related_objects`` here, the model
    ``mutations/resolvers.py::_raw_pk_relation_error``, and the serializer
    ``rest_framework/resolvers.py::_scope_specs_over_serializer``). ``None`` means
    "the related model has no registered primary ``DjangoType``" - a raw-pk relation
    with no visibility contract - and each caller keeps its OWN None-handling
    explicit (default-manager existence, an existence-only check, or skip), because
    that tail genuinely diverges per surface. Single-sites only the resolve + the
    visibility-scoping call, so the ONE place a drift is a data-leak bug class is
    written once (spec-039 Md3). An ``async def get_queryset`` met here raises
    ``SyncMisuseError`` (inherited from ``apply_type_visibility_sync``).
    """
    from ..registry import registry

    related_type = registry.get(related_model)
    if related_type is None:
        return None
    return visibility_scoped_related_queryset(related_type, info, async_recourse)


def related_visibility_queryset_or_default(
    related_model: type,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> models.QuerySet:
    """The visibility-scoped queryset, falling back to the default manager (DRY review C4).

    The "no primary ``DjangoType`` => default-manager, no visibility contract"
    fallback ``visible_related_object`` and ``visible_related_objects`` both
    opened with - a security-adjacent rule, now single-bodied: a related model
    with a registered primary is scoped through its ``get_queryset`` visibility
    hook; one without gets its plain ``_default_manager.all()`` (existence
    semantics only). Each caller keeps its own tail (``.filter(pk=pk).first()``
    vs the batched ``pk__in`` present-set).
    """
    queryset = related_visibility_queryset(related_model, info, async_recourse)
    if queryset is None:
        return related_model._default_manager.all()
    return queryset


def _stringified(pks: Any) -> set[str]:
    """Stringify a pk collection into the type-agnostic comparison basis (DRY review C5).

    The ``{str(pk) for pk in ...}`` coercion both membership helpers share, so
    the comparison basis (an int pk and its ``"3"`` string form compare equal -
    the GlobalID-in-filter string-explosion class) has exactly one body.
    """
    return {str(pk) for pk in pks}


def stringified_pks_present(queryset: models.QuerySet, query_pks: Any) -> set[str]:
    """Return the stringified pks among ``query_pks`` actually present in ``queryset`` (one query).

    The ``{str(pk) for pk in queryset.filter(pk__in=...).values_list("pk", flat=True)}``
    lookup the relation membership checks share (spec-039 Md4): the model
    ``mutations/resolvers.py::_relation_membership_error`` and the serializer
    ``visible_related_objects`` both build this present-set in one query, stringifying
    each pk for a type-agnostic membership compare (an int pk and its ``"3"`` string
    form compare equal). Single-sites the query + the str-coercion so the
    no-existence-leak comparison basis cannot drift.

    Inside an active write pipeline (``utils/write_transaction.py``) the query is
    pinned to the operation's write alias - a hook-re-routed queryset fails
    closed - and, when the operation locks (``Meta.select_for_update``), the
    membership read doubles as the relation-target row lock: a base-manager
    ``SELECT ... FOR UPDATE`` constrained by the (pinned) queryset's pk subquery,
    so an FK / M2M target confirmed visible here cannot be deleted out from under
    the write before the transaction commits. Read surfaces run with no pipeline
    context and are byte-unchanged.
    """
    pipeline = current_write_pipeline()
    if pipeline is not None:
        queryset = pin_write_queryset(queryset, pipeline.alias)
        if pipeline.lock:
            queryset = base_locked_queryset(queryset.model, pipeline.alias, queryset)
    return _stringified(queryset.filter(pk__in=list(query_pks)).values_list("pk", flat=True))


def pks_all_present(declared_pks: Any, present: set[str]) -> bool:
    """Return whether every ``declared_pks`` member (stringified) is in ``present`` (spec-039 Md4).

    The subset-membership test the model relation guard
    (``mutations/resolvers.py::_relation_membership_error``) and the serializer M2M
    decoder (``rest_framework/resolvers.py::_decode_relation_multi``) share: a
    ``declared`` set is fully present iff its stringified members are a subset of the
    ``present`` set (typically from ``stringified_pks_present``). A missing / hidden
    member fails the subset check, which each caller maps to the uniform field-keyed
    relation error - the same no-existence-leak outcome.
    """
    return _stringified(declared_pks) <= present


def visible_related_object(
    related_model: type,
    pk: Any,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> Any | None:
    """Resolve the VISIBLE related object by pk through the related primary's ``get_queryset``.

    The object-returning visibility-on-every-branch query, promoted from
    ``forms/resolvers.py::_visible_related_object`` (spec-039 P1.1) so the form AND
    serializer relation decoders share ONE implementation rather than forking a
    second object-returning decoder. Resolves the related model's primary
    ``DjangoType`` via the registry and runs the SAME visibility hook every read
    surface applies (``visibility_scoped_related_queryset`` =
    ``apply_type_visibility_sync(initial_queryset(...))``), so a writer cannot
    attach a row they could not *see*. Returns the visible object or ``None``
    (hidden / missing - the caller maps ``None`` to the field-keyed ``FieldError``,
    indistinguishable). The decoder needs the OBJECT (the form converts it to its
    ``to_field_name`` key; the serializer reduces it to the pk), which the ``036``
    ``_relation_visibility_error`` does not return, so it cannot call that helper -
    but it reuses the same primitives so the query shape is identical. An ``async
    def get_queryset`` met here raises ``SyncMisuseError``.

    The related model has a primary type only when a typed relation input was
    generated for it; a raw-pk relation's primary is resolved the same way
    (``registry.get``), and a model with no primary still resolves via the default
    manager (no visibility contract to apply). ``async_recourse`` stays a parameter:
    the form and serializer paths pass their own surface-specific wording, matching
    ``visibility_scoped_related_queryset``.

    The helper accepts a raw pk AFTER a flavor-specific decoder has chosen that
    branch; it does NOT imply every generated GraphQL relation input accepts both a
    raw pk and a GlobalID (the input exposes one strategy-dependent shape).
    """
    # The visibility-or-default-manager base is single-sited in
    # ``related_visibility_queryset_or_default`` (DRY review C4). Inside an
    # active write pipeline the read is pinned to the write alias (fail-closed on
    # a hook alias switch) and - when the operation locks - acquired as a
    # base-manager ``FOR UPDATE`` constrained by the visibility pk subquery, the
    # same relation-target lock the batched membership check applies.
    queryset = related_visibility_queryset_or_default(related_model, info, async_recourse)
    pipeline = current_write_pipeline()
    if pipeline is not None:
        queryset = pin_write_queryset(queryset, pipeline.alias)
        if pipeline.lock:
            queryset = base_locked_queryset(related_model, pipeline.alias, queryset)
    return queryset.filter(pk=pk).first()


def visible_related_objects(
    related_model: type,
    pks: Any,
    info: Any,
    async_recourse: str = _RELAY_ASYNC_RECOURSE,
) -> set:
    """Return the VISIBLE pks among ``pks`` in ONE visibility-scoped ``pk__in`` query (spec-039 rev6 #3).

    The BATCHED counterpart to ``visible_related_object``: instead of one visibility query per
    id (the per-element multi-relation decode), decode/type-check all ids first, then confirm
    the whole set's visibility in ONE ``pk__in`` query through the related primary
    ``DjangoType.get_queryset`` (or the target's default manager when no primary is registered -
    no visibility contract). Returns the set of pks actually visible (stringified for a
    type-agnostic membership compare); the caller asserts the REQUESTED set is a subset, so a
    hidden / missing member collapses to the same field-keyed relation error (no existence
    leak), exactly as the single decoder does. An ``async def get_queryset`` raises
    ``SyncMisuseError``. ``related_model`` has a primary type only when a typed relation input
    was generated for it; a raw-pk relation resolves its primary the same way (``registry.get``).
    """
    # The visibility-or-default-manager base is single-sited in
    # ``related_visibility_queryset_or_default`` (DRY review C4).
    queryset = related_visibility_queryset_or_default(related_model, info, async_recourse)
    return stringified_pks_present(queryset, pks)


async def apply_type_visibility_async(
    type_cls: type,
    queryset: models.QuerySet,
    info: Any,
) -> models.QuerySet:
    """Run ``type_cls.get_queryset`` in an async context, awaiting awaitables.

    Sync ``get_queryset`` returns the queryset directly and is passed
    through. Async ``get_queryset`` returns a coroutine which is awaited
    here before the caller's tail runs - the Decision 9 contract that an
    earlier implementation broke (it called the hook synchronously then
    invoked ``.filter`` on a coroutine).

    The hook is invoked once and AT MOST ONE returned awaitable is awaited;
    a second-level awaitable after that await is malformed (an ``async def``
    returning another coroutine / future) and fails closed - never a
    recursive await over an unbounded chain. The source and result then run
    the same shared hardened boundary as the sync runner
    (``_prepared_visibility_source`` / ``_normalized_visibility_result``),
    so the two colored paths cannot drift. ``SyncMisuseError`` stays
    reserved for sync boundaries: every defect here is a plain
    ``ConfigurationError``.
    """
    queryset, required_alias = _prepared_visibility_source(type_cls, queryset)
    result = type_cls.get_queryset(queryset, info)
    if inspect.isawaitable(result):
        result = await result
        if inspect.isawaitable(result):
            _dispose_sync_awaitable(result)
            raise ConfigurationError(
                f"{type_cls.__name__}.get_queryset resolved to a nested awaitable; an "
                f"async get_queryset must resolve to a QuerySet (or Manager) after ONE "
                f"await, and an unbounded awaitable chain is never consumed.",
            )
    # No identity fast path -- same contract as the sync runner: object identity
    # is not immutability, so a hook can mutate the sealed source's
    # ``_result_cache`` / ``_query`` and return it. The result is ALWAYS re-sealed
    # so the second seal drops any injected cache (``docs/feedback.md`` P1-2).
    return _normalized_visibility_result(type_cls, result, required_alias)


def reject_awaitable_sync_source(source: Any, type_cls: type) -> None:
    """Reject an awaitable source from a sync list or connection resolver.

    A plain ``def`` that returns an awaitable is committed to the sync field
    path. Passing that value onward would either skip queryset visibility or
    leak a Strawberry pagination error, so both field factories share this
    boundary.
    """
    if not inspect.isawaitable(source):
        return
    _dispose_sync_awaitable(source)
    raise SyncMisuseError(
        f"A sync {type_cls.__name__} consumer resolver returned an awaitable. "
        "Declare the resolver `async def` (or use an async callable) so the "
        "field awaits it and applies the get_queryset visibility hook; a plain "
        "`def` resolver that returns an awaitable is committed to the sync path "
        "and passing it through would silently skip get_queryset.",
    )


def reject_residual_async_source(source: Any, type_cls: type) -> None:
    """Reject a residual awaitable from an already-awaited async consumer resolver.

    Both async consumer pipelines await the consumer ``resolver=`` return
    exactly once before the value reaches source normalization: the list
    field's ``post_process_queryset_result_async`` and the connection field's
    ``connection.py::_pipeline_async``. A value that is STILL awaitable after
    that await is an ``async def`` resolver that resolved to another awaitable;
    it is neither a ``QuerySet`` nor a legitimate plain iterable, so the
    non-queryset branch would pass it through and silently SKIP the
    ``get_queryset`` visibility hook - a data-leak escape. The awaitable is
    disposed (never recursively awaited over an unbounded chain, matching the
    async runner's nested-awaitable handling) and the resolution fails closed.

    Single-sited here, beside ``reject_awaitable_sync_source`` (the sync twin),
    so the list and connection async pipelines cannot drift on the one boundary
    where a miss skips visibility - the connection pipeline previously lacked
    this guard, letting a nested async connection resolver bypass the hook.
    """
    if not inspect.isawaitable(source):
        return
    _dispose_sync_awaitable(source)
    raise ConfigurationError(
        f"An async {type_cls.__name__} consumer resolver resolved to another "
        f"awaitable after being awaited; a nested awaitable is neither a QuerySet "
        f"nor a plain iterable, and passing it through would silently skip the "
        f"get_queryset visibility hook. Return the queryset (or iterable) directly.",
    )


def post_process_queryset_result_sync(type_cls: type, result: Any, info: Any) -> Any:
    """Normalize a consumer-resolver return then apply visibility (sync).

    The list-field consumer-resolver shape: a ``Manager`` is coerced to a
    ``QuerySet`` (the field wrapper owns the coercion), a ``QuerySet`` runs the
    type's ``get_queryset`` visibility hook, and a non-queryset Python
    list / generator passes through unchanged. The default-resolver path bypasses
    this (its source is already ``initial_queryset(...)``, a known ``QuerySet``).

    An awaitable reaching here is rejected loudly through the single-sited
    ``reject_awaitable_sync_source`` guard, which keeps the invariant that a
    consumer ``QuerySet`` return is never resolved without its visibility hook.
    """
    reject_awaitable_sync_source(result, type_cls)
    source, is_queryset = normalize_query_source(result)
    if is_queryset:
        return apply_type_visibility_sync(type_cls, source, info)
    return source


async def post_process_queryset_result_async(type_cls: type, result: Any, info: Any) -> Any:
    """Async sibling of ``post_process_queryset_result_sync``.

    The caller awaits the consumer coroutine BEFORE handing the result here so
    the queryset branch sees the awaited value, not the coroutine itself. A
    RESIDUAL awaitable - an already-awaited async consumer resolver that
    resolved to another awaitable - fails closed through the shared
    ``reject_residual_async_source`` guard (also used by the connection async
    pipeline): it is neither a queryset nor a legitimate plain-iterable return,
    and passing it through the non-queryset branch would skip the
    ``get_queryset`` visibility hook.
    """
    reject_residual_async_source(result, type_cls)
    source, is_queryset = normalize_query_source(result)
    if is_queryset:
        return await apply_type_visibility_async(type_cls, source, info)
    return source
