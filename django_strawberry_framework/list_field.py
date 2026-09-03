"""``DjangoListField`` - non-Relay ``list[T]`` field for root Query fields.

Spec: ``docs/SPECS/spec-020-list_field-0_0_7.md``.
Target release: ``0.0.7``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from typing import Any

import strawberry
from strawberry.types import Info
from strawberry.utils.inspect import in_async_context

from .exceptions import (
    ConfigurationError,
    _safe_arg_repr,
    _safe_class_name,
)
from .resource_policy import bounded_rows, bounded_rows_async, validate_collection_bound
from .types import DjangoType
from .types.base import _is_relay_shaped
from .utils.directives import validated_field_directives
from .utils.querysets import (
    apply_type_visibility_async,
    apply_type_visibility_sync,
    initial_queryset,
    is_async_only_iterable,
    post_process_queryset_result_async,
    post_process_queryset_result_sync,
    reject_async_iterable_in_sync_context,
)
from .utils.typing import is_async_callable

__all__ = ("DjangoListField",)


# Consumer-resolver post-processing helpers. The field-wrapper Manager -> QuerySet
# coercion + visibility-hook contract is single-sited in
# ``utils/querysets.py::post_process_queryset_result_sync`` / ``_async``;
# these stay as the named consumer-wrapper entry points the
# ``_wrap`` resolvers call. The default-resolver path bypasses them because
# ``qs`` is already known to be a ``QuerySet`` from ``initial_queryset(...)`` -
# no normalization is needed there.


def _post_process_consumer_sync(target_type: type, result: Any, info: Info) -> Any:
    return post_process_queryset_result_sync(target_type, result, info)


async def _post_process_consumer_async(target_type: type, result: Any, info: Info) -> Any:
    return await post_process_queryset_result_async(target_type, result, info)


async def _bounded_async(
    awaitable: Any,
    info: Info,
    max_rows: int | None,
    *,
    trusted: bool,
) -> Any:
    """Await a visibility-applied result, then apply the field's row bound.

    The bound is applied LAST, never before the visibility hook. A sliced
    queryset cannot be refiltered or reordered, and both the visibility hook and
    the surface compose onto the source - so slicing first would turn the bound
    into a crash on every type that declares a hook. Ordering the two this way is
    a correctness constraint, not a preference.
    """
    return await bounded_rows_async(await awaitable, info, max_rows, trusted=trusted)


def _validate_djangotype_target(
    target_type: type,
    resolver: Callable | None,
    *,
    field: str,
) -> None:
    """Run the four shared DjangoType-target constructor guards for a field factory.

    Shared by ``DjangoListField`` and ``DjangoConnectionField`` (and any future
    node field). ``field`` is the factory's public name
    (e.g. ``"DjangoListField"``) interpolated into the ``ConfigurationError``
    messages so each factory's errors name itself. These four constructor-site
    checks fail at the line that wrote ``<field>(...)`` rather than at
    finalize-time.

    Order is load-bearing - each target-type check assumes the previous one
    passed. The third (own-class registration) check is the strict invariant:
    ``__django_strawberry_definition__`` is assigned by
    ``DjangoType.__init_subclass__`` (``types/base.py::DjangoType.__init_subclass__``)
    only for concrete subclasses carrying their own ``Meta`` with a ``model``.
    The attribute is inherited via MRO, so ``hasattr`` would accept a subclass
    that omits its own ``Meta`` - binding the field to a target whose
    definition, ``Meta.primary`` state, and model belong to the parent.
    ``definition.origin is target_type`` is the strict own-class invariant
    (NOT ``hasattr``).

    Every deployment-supplied value in a rejection message renders through the
    guarded helpers (``exceptions.py``): the non-class arm renders
    ``_safe_arg_repr`` (the ``_validate_mutation_target`` parity spelling) and
    the class arms render ``_safe_class_name``, so a hostile ``__repr__`` or a
    metaclass ``__name__`` property that raises cannot detonate the message
    assembly and replace the typed rejection with a raw ``RuntimeError``.

    The definition read is contained: ``getattr``'s default suppresses only
    ``AttributeError``, so a metaclass ``__getattr__`` raising anything else
    would escape raw and the typed "not a registered DjangoType" rejection
    would never exist. A read that cannot be answered is a target that cannot
    be PROVEN registered, so the failure is the same typed reject (fail
    closed, matching ``forms/inputs.py::_model_column_for``'s posture).

    Raises ``ConfigurationError`` on failure; returns the resolved
    ``__django_strawberry_definition__`` when all four pass, so the Relay
    validator consumes the SAME contained read instead of re-reading the
    attribute directly (a stateful metaclass could answer the first guarded
    read and detonate a second raw one). The caller runs any factory-specific
    guards (e.g. the connection field's Relay-Node guard) AFTER this returns.
    """
    if not inspect.isclass(target_type):
        raise ConfigurationError(
            f"{field} requires a DjangoType class; got {_safe_arg_repr(target_type)}.",
        )
    if not issubclass(target_type, DjangoType):
        raise ConfigurationError(
            f"{field} requires a DjangoType subclass; got {_safe_class_name(target_type)}.",
        )
    try:
        definition = getattr(target_type, "__django_strawberry_definition__", None)
    except Exception:
        # Contained: a metaclass whose __getattr__ raises anything other than
        # AttributeError must reach the typed rejection below, not escape raw.
        definition = None
    if definition is None or getattr(definition, "origin", None) is not target_type:
        raise ConfigurationError(
            f"{field} target {_safe_class_name(target_type)} is not a registered DjangoType. "
            f"This usually means {_safe_class_name(target_type)}'s `Meta` is missing a `model` "
            "declaration, or it inherits a definition from a parent without declaring its own `Meta`.",
        )
    if resolver is not None and not callable(resolver):
        raise ConfigurationError(f"{field} resolver must be callable.")
    return definition


def _validate_relay_djangotype_target(
    target_type: type,
    resolver: Callable | None,
    *,
    field: str,
    relay_error_message: str,
) -> None:
    """Run the four shared DjangoType-target guards plus the Relay-Node-shaped fifth.

    The Relay-shaped target guard shared by ``DjangoConnectionField`` and
    ``relay.py::_validate_node_target`` (which backs ``DjangoNodeField`` /
    ``DjangoNodesField``) -- single-sited. Delegates the
    four base checks to ``_validate_djangotype_target`` (with the call site's
    ``resolver`` seam), then rejects a non-Relay-Node-shaped target.
    ``_is_relay_shaped`` reads the declared ``Meta.interfaces`` (a
    Meta-declared ``relay.Node`` is in ``definition.interfaces`` before Phase
    2.5 injects it into ``__bases__``) OR direct ``relay.Node`` inheritance.
    The caller supplies the full ``relay_error_message`` so each factory keeps
    its own wording.
    """
    # The definition comes back from the base validator's ONE contained read;
    # re-reading the attribute directly here would let a stateful metaclass
    # answer the first (guarded, defaulted) read and detonate the second.
    definition = _validate_djangotype_target(target_type, resolver, field=field)
    if not _is_relay_shaped(target_type, definition.interfaces):
        raise ConfigurationError(relay_error_message)


# TODO(spec-050 slice 1): Add the list-argument record, typed error, wire-name
# lookup, and synthesized resolver signature before widening the field wrapper.
# Keep every helper in this module: it owns the arguments, while
# ``resource_policy.py`` owns only already-validated window coordinates.
#
# Pseudocode:
#
# - Define a frozen, slotted ``_ListArguments`` record carrying ``offset``,
#   ``limit``, ``effective_ceiling``, ``order_by``, ``order_by_supplied``, and
#   ``any_argument_supplied``. ``None`` and ``strawberry.UNSET`` are omission;
#   zero and an empty order list are supplied values. Keep the questions
#   SEPARATE and never read one field as a proxy for another:
#   ``any_argument_supplied`` selects argument mode and nothing else (so it is
#   what enables reject-combined); the window fields say which rows are
#   returned, and ``offset=0`` with no limit yields the omission window;
#   ``order_by_supplied`` -- never material activity -- drives
#   ``queryset_required``, because ``[]`` is still a supplied argument.
#   Material order activity is a fourth question answered only after public
#   apply succeeds.
# - Define ``ListArgumentError(GraphQLError,
#   DjangoStrawberryFrameworkError)`` with no N818 suppression. It is PUBLIC:
#   export it from the package root beside ``ResourceLimitExceeded`` and
#   ``SyncMisuseError`` and update ``tests/base/test_init.py``'s pinned
#   ``__all__`` tuple, star-import row, export-identity row, and its stale
#   comment claiming the 0.0.15 cut leaves the public surface unchanged. The
#   version literal and its own assertion stay with card 053. Its constructor
#   alone builds the message and ``LIST_ARGUMENT_INVALID`` extensions. Preserve
#   field/argument/reason/value/ceiling attributes and implement ``__reduce__``
#   as ``(self.__class__, complete_constructor_args, self.__dict__)`` so the
#   dual-base error round-trips without relying on GraphQLError's slots.
#   Numeric ``negative`` failures carry ``value``; ``over_ceiling`` carries
#   ``value`` plus ``ceiling``; direct-call ``non_integer`` carries the safe
#   ``describe_value`` string; ``order_required`` carries the rejected offset;
#   ``queryset_required`` carries neither optional key. The message names the
#   active GraphQL field and argument, but never serializes order input.
# - Resolve a Python parameter's wire name through
#   ``info.get_argument_definition(parameter)`` plus
#   ``schema_config_from_info(info).name_converter.from_argument(...)``. Fall
#   back only for direct helper calls without a real schema: ``offset``,
#   ``limit``, and default-converted ``orderBy``. Resolve LAZILY, inside the
#   error constructor only: a successful request must perform ZERO name
#   conversions. ``from_argument`` is a consumer hook normally run once per
#   argument at schema-construction time, so calling it per resolver
#   invocation both wastes work and invokes a shared, possibly stateful
#   converter concurrently at runtime, where a non-deterministic one could
#   report a spelling the built schema does not use. Pin the zero-call count on
#   success and the one-call count on rejection.
# - Normalize offset before limit. Reject bool/non-int direct calls as
#   ``non_integer`` with ``describe_value``; reject negatives and values above
#   their ceilings as ``negative`` / ``over_ceiling``. Compute the return cap
#   only through ``effective_bound(policy.max_list_rows, max_rows,
#   trusted=trusted_max_rows)``; offset always uses ``policy.max_list_rows``.
# - Build one signature from reserved positional-or-keyword ``root=None``
#   followed by keyword-only ``info``, ``offset: int | None``, and
#   ``limit: int | None``. If the target definition has ``orderset_class``, add keyword-only
#   ``order_by: list[order_input_type(orderset_class)] | None``. Keep the
#   ``order_input_type`` import local, assign both ``__signature__`` and
#   ``__annotations__``, and do not synthesize a return annotation: the
#   consumer's class-attribute annotation remains the nullability owner.
# - The executable wrapper must accept the synthesized keywords itself and
#   never forward them to ``resolver=``; consumer resolvers remain exactly
#   ``resolver(root, info)``.
#
# TODO(spec-050 slice 2): Replace the current wrapper tails with one colored
# visibility -> order -> guard -> window pipeline while preserving the exact
# all-null/omitted fast path.
#
# Pseudocode:
#
# - Validate scalar/cap arguments before invoking a consumer resolver. Then run
#   the current await-once/dispose-on-misuse source logic and Manager coercion.
# - When ``has_active_arguments`` is false, preserve the current colored call
#   exactly: sync uses ``bounded_rows(...)`` and async uses
#   ``bounded_rows_async(...)`` after its current visibility path. Do not
#   rebuild an equivalent ``offset=0`` window on this branch.
# - On a non-queryset, reject any non-null ``order_by`` first with
#   ``queryset_required``. Reject ``offset > 0`` second with
#   ``order_required``. Before either async-only-source rejection escapes,
#   acquire and close its iterator through resource_policy's shared cleanup
#   helper without advancing it; attach acquisition/close failures as notes.
# - On a queryset, apply visibility with the argument-aware reject-combined
#   policy. If order input was supplied, dispatch through the target
#   ``OrderSet.apply_sync`` / ``apply_async`` exactly once, enforce the async
#   method's await-once contract, and pass its result to querysets' shared
#   post-order seal. Never inspect consumer queryset state in this module.
# - Ask ``OrderSet._input_has_active_terms`` only after public apply succeeds.
#   For active input, require ``queryset.ordered`` and reject an exact ``?`` or
#   recognized ``Random()``/``OrderBy(Random())`` term. For model-default
#   fallback require non-empty stable ``query.get_meta().ordering``,
#   ``query.default_ordering is True``, empty ``query.order_by`` and
#   ``query.extra_order_by``, and falsy ``query.group_by`` exactly as Django's
#   own rule spells it. A hidden resolver order is not fallback evidence.
#   Reject everything else with ``order_required``; append neither pk nor
#   DISTINCT. One private random-term predicate serves both explicit and
#   model-default checks; do not duplicate expression recognition.
# - Hand validated ``offset`` / ``limit`` to the one resource-policy bound.
#   Under async execution, wrap every final queryset in querysets' async-only
#   completion adapter. This includes a plain ``def`` consumer returning a
#   Manager/QuerySet: keep its sync visibility color, then adapt the final
#   queryset based on runtime execution context. Lists, ``None``, and genuine
#   async-only iterables retain their existing result shapes.
#
# TODO(spec-050 slice 5): Replace the complete Ordering contract and Row bound
# paragraphs in ``DjangoListField``'s docstring when the arguments ship. State
# conditional Meta-derived ``orderBy``, active schema naming, both ceilings,
# nonzero-offset ordering, no pk append, and the unique-final-term guidance.
# Name the contract ORDERED OFFSET, never stable or repeatable pagination: an
# active order fixes the sort expression, not which of two tied rows falls on
# either side of the boundary. Say that a published ``offset`` is a RUNTIME
# PRECONDITION -- usable only where an order source exists, permanently
# rejecting positive values on a target with neither ``Meta.orderset_class``
# nor still-effective model ``Meta.ordering`` -- not a claim the field can
# page. Both ceilings are ACCEPTED COORDINATE ceilings, not scan budgets.
def DjangoListField(  # noqa: N802  # PascalCase for graphene-django parity - consumer usage is `DjangoListField(BranchType)`
    target_type: type,
    *,
    resolver: Callable | None = None,
    description: str | None = None,
    deprecation_reason: str | None = None,
    directives: Sequence[object] = (),
    max_rows: int | None = None,
    trusted_max_rows: bool = False,
) -> Any:
    """Factory for a non-Relay ``list[T]`` root Query field bound to a ``DjangoType``.

    See ``docs/SPECS/spec-020-list_field-0_0_7.md`` Decision 1 (mechanism) and
    Decision 2 (default-resolver shape) for the design contract.

    Ordering contract: a ``DjangoListField`` does NOT guarantee row order unless
    the query supplies an ``orderBy`` argument or the model declares
    ``Meta.ordering``. The default resolver returns
    ``model._default_manager.all()`` with no tiebreaker, so the response array
    order is database-dependent. This is intentional and asymmetric with
    ``DjangoConnectionField``, which appends a pk tiebreaker to guarantee a
    deterministic total order (its positional cursors require one); a flat list
    has no cursors, so the unordered sequence is acceptable.

    Row bound (spec-047 Decision 6). Every ``DjangoListField`` is bounded: the
    request's ``ResourcePolicy.max_list_rows`` applies whether or not the field
    says anything, and ``max_rows=`` narrows it further for this field. There is
    no unbounded spelling - ``max_rows=None`` means "the policy governs", not
    "no bound". ``trusted_max_rows=True`` is the explicit widening opt-in: it
    declares that this field's ``max_rows`` is a deliberate declaration that
    outranks the request policy, and it is the only way a field can be wider
    than the policy.
    """
    if max_rows is not None:
        validate_collection_bound(max_rows, field="DjangoListField max_rows")
    # Decision 5 validation guards: the four shared DjangoType-target
    # constructor checks (see ``_validate_djangotype_target`` for the
    # load-bearing ordering and the own-class registration invariant).
    _validate_djangotype_target(target_type, resolver, field="DjangoListField")
    # The hostile-container containment for the directives iterable, shared with
    # every other field factory in the package
    # (``utils/directives.py::validated_field_directives`` owns the one check and
    # its rationale): a bare string / bytes is iterated element-wise by
    # Strawberry, a hostile iterator raising midway escapes raw, and a
    # non-iterable detonates at the ``strawberry.field`` call. Validate BEFORE
    # handing to Strawberry so the factory fails loud as a ``ConfigurationError``
    # at the assignment line. ``utils.directives`` imports only ``exceptions``,
    # so the low-level read-side module can share it without the read->write
    # layering inversion importing the mutations copy would have created.
    directives = validated_field_directives("DjangoListField", directives)
    # Async-detection asymmetry (see spec Decision 2,
    # "Async-detection asymmetry - intentional, not a harmonization candidate"):
    # ``_default`` uses runtime ``in_async_context()`` per-call so the same
    # factory output dispatches correctly under both ``schema.execute_sync``
    # and ``await schema.execute``. The consumer-wrapper branch below commits
    # per-construction via ``is_async_callable(user_resolver)`` (the
    # ``__call__``/``functools.partial``-aware superset of
    # ``inspect.iscoroutinefunction``) because Strawberry inspects the resolver
    # signature once at schema
    # construction and freezes the sync-vs-async handling.
    if resolver is None:

        def _default(root: Any, info: Info) -> Any:  # noqa: ARG001
            qs = initial_queryset(target_type)
            if in_async_context():
                # The async branch DOES need its own coroutine wrapper: the row
                # bound has to be applied to the awaited value, after the
                # visibility hook has composed onto the unsliced source.
                return _bounded_async(
                    apply_type_visibility_async(target_type, qs, info),
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                )
            return bounded_rows(
                apply_type_visibility_sync(target_type, qs, info),
                info,
                max_rows,
                trusted=trusted_max_rows,
            )

        wrapped = _default
    else:
        user_resolver = resolver

        async def _resolve_async_iterable(source: Any, info: Info) -> Any:
            return await bounded_rows_async(
                await _post_process_consumer_async(target_type, source, info),
                info,
                max_rows,
                trusted=trusted_max_rows,
            )

        if is_async_callable(user_resolver):

            async def _wrap(root: Any, info: Info) -> Any:
                # ``await`` the consumer coroutine BEFORE handing
                # the result to ``_post_process_consumer_async`` so the
                # isinstance-QuerySet branch sees the awaited value, not the
                # coroutine itself. The row bound is applied AFTER
                # post-processing, so a returned ``Manager`` has already been
                # coerced to a ``QuerySet`` and the visibility hook has already
                # composed onto the unsliced source.
                return await bounded_rows_async(
                    await _post_process_consumer_async(
                        target_type,
                        await user_resolver(root, info),
                        info,
                    ),
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                )
        else:
            # ONE sync body serves a plain ``def`` resolver AND a declared
            # async-generator resolver (the same committed posture the
            # connection field's sync branch documents): calling either always
            # yields a NON-awaitable value here, and an async-only return is
            # classified by VALUE at call time - completed through the async
            # bound under async execution, rejected through the shared
            # sync-misuse guard otherwise. No declared-shape check is needed:
            # calling an async-generator callable (bare, ``partial``-wrapped,
            # or an async-gen ``__call__`` instance) always produces an
            # async-only iterable.

            def _wrap(root: Any, info: Info) -> Any:
                source = user_resolver(root, info)
                if is_async_only_iterable(source):
                    reject_async_iterable_in_sync_context(
                        source,
                        flavor_noun="DjangoListField",
                    )
                    return _resolve_async_iterable(source, info)
                return bounded_rows(
                    _post_process_consumer_sync(target_type, source, info),
                    info,
                    max_rows,
                    trusted=trusted_max_rows,
                )

        wrapped = _wrap

    return strawberry.field(
        resolver=wrapped,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
