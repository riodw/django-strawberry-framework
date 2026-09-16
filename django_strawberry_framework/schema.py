"""``DjangoSchema`` - the schema whose mutation transactions span response completion.

The 0.0.14 mutation-atomicity commit-gap fix. A generated mutation's write pipeline runs inside
``transaction.atomic()``, but graphql-core *completes* (serializes) the returned
payload only after the resolver returns - historically after that transaction had
already committed. A completion failure (a non-nullable field resolving ``null``,
a corrupt scalar) therefore surfaced as ``data: null`` + a top-level error while
the write stayed committed: the client is told the mutation failed, the database
says it succeeded.

``DjangoMutationExecutionContext`` closes the gap at the only layer that sees
both sides: for each TOP-LEVEL generated mutation field it opens one
``transaction.atomic(using=<write alias>)`` BEFORE the resolver runs and exits it
only after graphql-core finished completing that field's value. Any error added
to the execution during that window - resolver-raised or completion-raised -
marks the transaction for rollback, so an unserializable payload rolls the write
back. The window also publishes the managed alias
(``utils/write_transaction.py::managed_write_transaction``), which the write pipeline
REQUIRES: a generated mutation executed through a plain ``strawberry.Schema``
fails before any database work, directing the consumer here.

Execution-mode split (spec plan "Implementation Changes"):

- **Sync** (``schema.execute_sync`` / the WSGI view): graphql-core completes the
  field synchronously inside ``execute_field``, so the context holds the
  transaction directly around the ``super()`` call on the calling thread.
- **Async** (``await schema.execute`` / ASGI / Channels): the ORM pipeline runs
  in ``sync_to_async(thread_sensitive=True)`` workers, and asgiref routes every
  ``thread_sensitive`` call from one async context onto the SAME thread - so the
  context opens the transaction in one such worker, awaits the field's
  completion, and closes it in another; open, pipeline, and close all share one
  thread and therefore one Django connection. Because the default
  thread-sensitive executor is process-wide, a process-wide lock per write alias
  serializes these completion-spanning windows across event loops; concurrent
  requests cannot accidentally nest savepoints on that shared connection.

Mutation root fields execute serially (the GraphQL spec's mutation semantics,
graphql-core's ``execute_fields_serially``), so consecutive top-level mutation
fields get INDEPENDENT transactions: field two's transaction opens only after
field one's committed or rolled back.

Only fields whose resolver carries the ``DjangoMutationField`` marker are
wrapped; every other field (queries, consumer-written mutations, introspection)
executes exactly as stock graphql-core.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, replace
from typing import Any

import strawberry
from django.db import transaction
from graphql import GraphQLError
from graphql.execution.execute import ExecutionContext
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.inspect import in_async_context

from .error_policy import DEFAULT_ERROR_POLICY, ErrorPolicy, resolve_error_policy
from .exceptions import ConfigurationError
from .extensions.error_policy import DjangoErrorPolicyExtension
from .extensions.resource_policy import DjangoResourcePolicyExtension, _AdmissionGuard
from .mutations.fields import MUTATION_CLASS_MARKER
from .resource_policy import DEFAULT_RESOURCE_POLICY, ResourcePolicy, resolve_resource_policy
from .utils.policies import copy_policy
from .utils.private_state import PrivateAuthority, PrivateMembership
from .utils.querysets import run_in_one_sync_boundary
from .utils.write_transaction import managed_write_transaction, resolve_write_alias


class _AcquireHandoff:
    """Ownership hand-off between an executor thread and the task awaiting it.

    ``asyncio.to_thread`` cannot stop a thread already blocked in
    ``threading.Lock.acquire``, so a CANCELLED acquisition has two possible
    orderings and both must end with the mutex unowned rather than held by a
    transaction window that no longer exists: the thread may take the mutex
    after the awaiting task gave up, or the task may give up after the thread
    already took it. Each side records itself here under one guard, so exactly
    one of them observes the other and performs the release.
    """

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._acquired = False
        self._abandoned = False

    def acquired(self) -> bool:
        """Record the thread's acquisition; ``True`` when the waiter already left."""
        with self._guard:
            self._acquired = True
            return self._abandoned

    def abandon(self) -> bool:
        """Record the waiter's cancellation; ``True`` when the thread already acquired."""
        with self._guard:
            self._abandoned = True
            return self._acquired


class _AsyncAliasLock:
    """An async context manager for a process-wide, cross-event-loop mutex."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def _acquire_for(self, handoff: _AcquireHandoff) -> None:
        """Take the mutex on the executor thread, releasing it if nobody is left."""
        self._lock.acquire()
        if handoff.acquired():
            self._lock.release()

    async def __aenter__(self) -> _AsyncAliasLock:
        handoff = _AcquireHandoff()
        acquire = asyncio.create_task(asyncio.to_thread(self._acquire_for, handoff))
        cancelled: asyncio.CancelledError | None = None
        while not acquire.done():
            try:
                await asyncio.shield(acquire)
            except asyncio.CancelledError as exc:  # noqa: PERF203 - repeated cancellation hand-off loop
                # The executor thread cannot be cancelled while it waits on the
                # mutex, so keep awaiting the hand-off across REPEATED
                # cancellations - returning here would leave the acquisition
                # ownerless. A cancellation of the acquiring task itself (loop
                # teardown) ends the loop through ``acquire.done()`` instead of
                # spinning, and the hand-off still disposes of the ownership
                # that uncancellable thread is about to take.
                cancelled = exc
        if cancelled is not None:
            if handoff.abandon():
                self._lock.release()
            # Preserve cancellation so the next operation cannot inherit
            # ownership of a window this task never entered.
            raise cancelled
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc: Any,
        traceback: Any,
    ) -> None:
        del exc_type, exc, traceback
        self._lock.release()


_ASYNC_MUTATION_LOCKS: dict[str, _AsyncAliasLock] = {}
_ASYNC_MUTATION_LOCKS_GUARD = threading.Lock()


def _async_mutation_lock(alias: str) -> _AsyncAliasLock:
    """Return the process/alias lock guarding one async transaction window.

    ``thread_sensitive=True`` uses one process-wide worker when no explicit
    ``ThreadSensitiveContext`` exists. An outer transaction that spans an
    ``await`` would therefore let a concurrent mutation enter a nested savepoint
    on the same connection. Serializing only mutation windows for the same
    effective alias preserves one-connection atomicity without creating a
    short-lived worker (and leaking in-memory SQLite connections); distinct
    aliases retain independent concurrency. The mutex is process-wide because
    separate event loops still share that worker.
    """
    with _ASYNC_MUTATION_LOCKS_GUARD:
        return _ASYNC_MUTATION_LOCKS.setdefault(alias, _AsyncAliasLock())


class DjangoMutationExecutionContext(ExecutionContext):
    """Hold each generated mutation field's transaction open through value completion."""

    def execute_field(
        self,
        parent_type: Any,
        source: Any,
        field_nodes: Any,
        path: Any,
    ) -> Any:
        """Wrap a marked top-level mutation field in its completion-spanning transaction."""
        mutation_cls = self._marked_mutation_class(parent_type, field_nodes)
        if mutation_cls is None:
            return super().execute_field(parent_type, source, field_nodes, path)

        model = getattr(getattr(mutation_cls, "_mutation_meta", None), "model", None)
        alias = resolve_write_alias(model)
        if in_async_context():
            return self._execute_mutation_field_async(
                alias,
                parent_type,
                source,
                field_nodes,
                path,
            )
        return self._execute_mutation_field_sync(alias, parent_type, source, field_nodes, path)

    def _marked_mutation_class(self, parent_type: Any, field_nodes: Any) -> type | None:
        """Return the field's bound mutation class, or ``None`` for any unmarked field.

        Only TOP-LEVEL mutation fields qualify (``parent_type`` is the schema's
        mutation root; ``execute_field`` also fires for every nested payload
        field, whose completion the already-open transaction covers). The marker
        is read through Strawberry's field extension
        (``extensions["strawberry-definition"].base_resolver.wrapped_func``) -
        the synthesized ``_resolve`` the ``DjangoMutationField`` factory stamped
        with its mutation class.
        """
        if (
            parent_type is None
            or self.schema.mutation_type is None
            or parent_type is not self.schema.mutation_type
        ):
            return None
        if not field_nodes:
            return None
        field_node = field_nodes[0]
        node_name = getattr(field_node, "name", None)
        field_name = getattr(node_name, "value", None)
        if not field_name:
            return None
        parent_fields = getattr(parent_type, "fields", None)
        if not isinstance(parent_fields, dict):
            return None
        field_def = parent_fields.get(field_name)
        if field_def is None:  # introspection (``__typename``) has no field entry here.
            return None
        strawberry_field = (getattr(field_def, "extensions", None) or {}).get(
            "strawberry-definition",
        )
        base_resolver = getattr(strawberry_field, "base_resolver", None)
        wrapped = getattr(base_resolver, "wrapped_func", None)
        return getattr(wrapped, MUTATION_CLASS_MARKER, None)

    def _execution_errors(self) -> list:
        """Return the execution's live error list across graphql-core versions.

        graphql-core < 3.2.9 stores located errors directly as
        ``ExecutionContext.errors`` (a plain list); 3.2.9 replaced that
        attribute with a ``CollectedErrors`` container exposing the same list
        as ``collected_errors.errors``. Both are append-only during execution,
        so a before/after length comparison stays valid on either shape.
        """
        collected = getattr(self, "collected_errors", None)
        if collected is not None:
            return getattr(collected, "errors", [])
        return getattr(self, "errors", [])

    def _rollback_for_new_errors(self, errors_before: int, alias: str) -> None:
        """Roll the window's transaction back when execution collected new errors.

        The ONE statement of the window's failure rule, consulted by both
        execution modes: any located error added to the execution during the
        completion-spanning window - resolver-raised or completion-raised -
        marks the transaction for rollback before it exits. A resolver failure
        is a *located* error, not an exception, so an exception-based rollback
        would miss it; the before/after length comparison over
        ``_execution_errors`` stays valid on either of graphql-core's
        error-container shapes because both are append-only during execution.

        An UNREADABLE container (a raising ``errors`` access or ``__len__``)
        cannot certify the window stayed error-free, so it fails closed: the
        rollback is marked here and the read's failure re-raised, letting the
        caller's ``finally`` exit the atomic - the write is rolled back and the
        failure surfaces, never a commit behind an uncertified window.
        """
        try:
            errors_now = len(self._execution_errors())
        except Exception:
            transaction.set_rollback(True, using=alias)
            raise
        if errors_now > errors_before:
            transaction.set_rollback(True, using=alias)

    def _execute_mutation_field_sync(
        self,
        alias: str,
        parent_type: Any,
        source: Any,
        field_nodes: Any,
        path: Any,
    ) -> Any:
        """Sync execution: hold the transaction directly around resolve + completion.

        Under sync execution graphql-core completes the field's value INSIDE the
        ``super().execute_field`` call, so entering ``transaction.atomic`` before
        it and exiting after covers the whole resolve -> complete window on the
        calling thread. New errors collected during the window roll it back
        through ``_rollback_for_new_errors`` before the block exits.
        """
        errors_before = len(self._execution_errors())
        atomic = transaction.atomic(using=alias)
        atomic.__enter__()
        try:
            with managed_write_transaction(alias):
                result = super().execute_field(parent_type, source, field_nodes, path)
        except BaseException as exc:
            if not atomic.__exit__(type(exc), exc, exc.__traceback__):
                raise
            return None  # pragma: no cover - ``atomic.__exit__`` never suppresses.
        try:
            self._rollback_for_new_errors(errors_before, alias)
        finally:
            # The window's atomic exits even when the rollback decision itself
            # raises, so a hostile error container cannot abandon an open
            # transaction on the connection.
            atomic.__exit__(None, None, None)
        return result

    async def _execute_mutation_field_async(
        self,
        alias: str,
        parent_type: Any,
        source: Any,
        field_nodes: Any,
        path: Any,
    ) -> Any:
        """Async execution: open / close the transaction in the ``thread_sensitive`` worker.

        The ORM pipeline runs in ``sync_to_async(thread_sensitive=True)`` (the
        spec-036 one-worker boundary), and asgiref serializes every
        ``thread_sensitive`` call from this async context onto the SAME thread -
        so ``__enter__`` here, the pipeline's queries, and ``__exit__`` below all
        share one thread and one Django connection. The completion ``await``
        happens between them on the event loop; the transaction stays open on the
        worker's (idle) connection meanwhile.
        """
        # ``thread_sensitive=True`` otherwise falls back to asgiref's one
        # process-wide worker. Keeping a transaction open across the completion
        # await there would let a second concurrent operation enter a nested
        # savepoint on the same connection, coupling its commit/rollback to the
        # first request. The lock is process-wide per effective write alias, so
        # the existing worker/connection stays reusable while concurrent
        # transactions on different aliases remain independent.
        async with _async_mutation_lock(alias):
            errors_before = len(self._execution_errors())
            atomic = transaction.atomic(using=alias)
            await run_in_one_sync_boundary(atomic.__enter__)
            try:
                with managed_write_transaction(alias):
                    result = super().execute_field(parent_type, source, field_nodes, path)
                    if self.is_awaitable(result):
                        result = await result
            except BaseException as exc:
                # Bind the exception explicitly: the ``except`` name is cleared when
                # the block exits, so the worker-thread closure must not capture it.
                captured = exc

                def _exit_with_error() -> bool:
                    return bool(atomic.__exit__(type(captured), captured, captured.__traceback__))

                if not await run_in_one_sync_boundary(_exit_with_error):
                    raise
                return None  # pragma: no cover - ``atomic.__exit__`` never suppresses.

            def _exit_clean() -> None:
                try:
                    self._rollback_for_new_errors(errors_before, alias)
                finally:
                    # Mirror of the sync guard: the atomic exits even when the
                    # rollback decision raises, so the alias lock is never
                    # released over an abandoned open transaction.
                    atomic.__exit__(None, None, None)

            await run_in_one_sync_boundary(_exit_clean)
            return result


#: The wire-visible ``extensions.code`` on an operation refused because the
#: schema cannot enforce what it was configured with. Distinct from a resource
#: rejection: nothing about the request is over budget, and no policy of the
#: deployment's was applied to it.
SCHEMA_CONFIGURATION_ERROR_CODE = "SCHEMA_CONFIGURATION_UNAVAILABLE"


@dataclass(frozen=True)
class _SchemaEnforcement:
    """What one ``DjangoSchema`` construction settled, held where no name on it reaches.

    The two resolved policies, the record of which enforcement extensions this
    constructor had to install itself, and whether the base constructor has
    settled the extension configuration yet. Every field is a policy of
    primitives or a flag, so the record points at nothing: it can be held for
    the schema without keeping the schema alive.
    """

    resource_policy: ResourcePolicy
    error_policy: ErrorPolicy
    auto_resource_extension: bool
    auto_error_extension: bool
    extensions_settled: bool = False


#: Every ``DjangoSchema``'s enforcement record, held here and by nothing else.
#:
#: An instance attribute cannot hold this. ``info.schema`` is handed to every
#: resolver in every operation, so an ordinary ``self._resource_policy`` entry
#: is a name any resolver can assign - directly, or through ``schema.__dict__``
#: past a property that has no setter - and the schema is process-lived, so one
#: such write widens or disarms every later request the process serves rather
#: than the one that made it. Nor is holding the record behind an attribute and
#: checking its identity enough: the record answered from an attribute is a
#: record a resolver can reach, and reaching a frozen dataclass is enough to
#: write it (``policy.__dict__[bound] = wider``).
#:
#: So no attribute answers with it at all. Holding it here is what the record's
#: own shape permits: two policies and two flags point at nothing, so this
#: mapping retains a schema's configuration without retaining the schema, and
#: the weak reference filed beside each record drops the entry when its schema
#: dies. The arbitrary extension graph, which does point back, is held the other
#: way (:data:`_SCHEMA_EXTENSIONS`).
_SCHEMA_ENFORCEMENT: PrivateAuthority[_SchemaEnforcement] = PrivateAuthority()

#: Every ``DjangoSchema``'s accepted extension configuration, held by the schema
#: it belongs to.
#:
#: This one cannot live beside the enforcement record, and the reason has
#: nothing to do with resolvers: the entries are consumer objects that reach the
#: schema back - an extension instance through the execution context, and
#: ``extensions=[self.make_extension]`` directly - so a module-global holding
#: them strongly would keep every such schema, its last execution context and
#: that request's variables alive for the life of the process.
#:
#: The schema therefore holds them, and
#: ``utils/private_state.py::PrivateMembership`` holds one weak reference per
#: accepted ENTRY - which is the granularity the question is asked at. What
#: decides whether the next operation is bounded is not which object the
#: attribute answers with but which extensions are inside it, so evidence about
#: a carrier would certify nothing: writing new entries into one leaves its
#: identity exactly as accepted. Each operation therefore resolves the entries
#: the evidence points at, and an entry written over the attribute is one this
#: schema never accepted and never runs.
#:
#: What the attribute still does is hold those entries alive, and that is the
#: one thing a write to it can take away. An entry the deployment kept no other
#: reference to is collected, its evidence stops resolving, and the accepted
#: configuration cannot be reconstructed - a consumer entry carrying a narrow
#: policy of its own is one the package has no other copy of, and a factory's
#: policy it never saw at all. :meth:`DjangoSchema.get_extensions` refuses the
#: operation there rather than resolving a list it cannot vouch for, because
#: falling back to this schema's own policy would answer a lost entry with a
#: wider budget.
_SCHEMA_EXTENSIONS: PrivateMembership[Any] = PrivateMembership("_django_extensions")

#: The record answered for a schema that never completed ``DjangoSchema.__init__``
#: - a subclass that skipped ``super().__init__``, or an object whose
#: construction raised. Such a schema declared nothing, so the package defaults
#: bound its requests and the masking error policy applies, and both extensions
#: count as automatic so a consumer entry still wins the deduplication. This is
#: not a fallback for a configuration that was tampered with: a settled record
#: cannot go missing while its schema is alive.
_FALLBACK_ENFORCEMENT = _SchemaEnforcement(
    resource_policy=DEFAULT_RESOURCE_POLICY,
    error_policy=DEFAULT_ERROR_POLICY,
    auto_resource_extension=True,
    auto_error_extension=True,
)


def _enforcement(schema: Any) -> _SchemaEnforcement:
    """The record ``schema`` was settled with, or the record of one that settled none."""
    record = _SCHEMA_ENFORCEMENT.recall(schema)
    return _FALLBACK_ENFORCEMENT if record is None else record


class _RefusedConfiguration(SchemaExtension):
    """Refuse every operation on a schema whose accepted extensions cannot be read back.

    Installed in place of the extension chain when the configuration a schema
    was constructed with was replaced or deleted behind the attribute holding
    it. Running the operation anyway would mean enforcing something other than
    what the deployment accepted, and the entries that are missing are the only
    record of what they declared.

    The refusal is PUBLISHED as this request's pre-execution error and restated
    where execution would begin, which is the pair of seams every transport
    renders - the same shape a resource rejection uses, for the same reason: an
    exception out of a hook leaves a streaming operation with no frame at all.
    """

    def on_parse(self) -> Iterator[None]:
        """Publish the refusal once the document exists, before anything validates it."""
        yield
        self.execution_context.validation_rules = ()
        self.execution_context.pre_execution_errors = [self._refusal()]

    def on_validate(self) -> Iterator[None]:
        """Restate the refusal, before the check upstream makes inside this stage."""
        self.execution_context.pre_execution_errors = [self._refusal()]
        yield

    def on_execute(self) -> None:
        """Refuse to begin executing, for a path that reached execution regardless."""
        raise self._refusal()

    def _refusal(self) -> GraphQLError:
        """The error this schema answers every operation with."""
        return GraphQLError(
            "The schema's accepted extension configuration could not be read back, "
            "so the operation cannot be enforced as configured.",
            extensions={"code": SCHEMA_CONFIGURATION_ERROR_CODE},
        )


class DjangoSchema(strawberry.Schema):
    """``strawberry.Schema`` with the mutation-transaction execution context installed.

    The REQUIRED schema class for any schema exposing generated mutations
    (``DjangoMutationField`` targets): the write pipeline refuses to run outside
    the managed transaction this schema's execution context opens. Drop-in
    otherwise - every constructor argument passes through, and a consumer
    needing a custom execution context subclasses
    ``DjangoMutationExecutionContext`` and passes it explicitly.

    **The execution resource policy is resolved here, once.** ``resource_policy=``
    accepts a ``ResourcePolicy`` or a mapping of bound names to values; omitted,
    the ``DJANGO_STRAWBERRY_FRAMEWORK["RESOURCE_POLICY"]`` setting and then the
    package defaults apply. The resolved object is validated at construction - an
    invalid bound fails the deployment at startup, not on a request - is exposed
    as ``schema.resource_policy``, and is enforced by
    ``extensions/resource_policy.py::DjangoResourcePolicyExtension``, which this
    constructor appends unless the consumer already supplied one. A schema built
    through this class is therefore bounded with no opt-in boilerplate, which is
    the whole point: an endpoint whose only limiter is one a consumer remembered
    to install is an endpoint with no limiter.

    **The production error policy is resolved here too, and by the same rule.**
    ``error_policy=`` accepts an ``ErrorPolicy`` or a mapping of option names to
    values; omitted, the ``DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]`` setting
    and then the package defaults apply. It is validated at construction, exposed
    as ``schema.error_policy``, and enforced by
    ``extensions/error_policy.py::DjangoErrorPolicyExtension``, which this
    constructor PREPENDS unless the consumer already supplied one - the position
    is load-bearing, see ``_with_error_policy_extension``. Under
    ``settings.DEBUG = False`` an unexpected resolver or hook exception therefore
    reaches the client as a stable message plus a correlation identifier rather
    than as whatever the exception happened to say. Opting out is explicit:
    ``DjangoSchema(error_policy={"enabled": False})``.
    """

    def __init__(
        self,
        *args: Any,
        resource_policy: ResourcePolicy | Mapping[str, Any] | None = None,
        error_policy: ErrorPolicy | Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        resolved_resource = resolve_resource_policy(resource_policy)
        resolved_error = resolve_error_policy(error_policy)
        if kwargs.get("execution_context_class") is None:
            kwargs["execution_context_class"] = DjangoMutationExecutionContext
        extensions, auto_resource = _with_resource_policy_extension(kwargs.get("extensions"))
        auto_error = not any(
            _extension_entry_matches(extension, DjangoErrorPolicyExtension)
            for extension in extensions
        )
        kwargs["extensions"] = _with_error_policy_extension(extensions)
        if _SCHEMA_ENFORCEMENT.settled(self):
            # A constructed schema is reachable from every resolver it serves,
            # and so is its ``__init__``. Running it again would replace the
            # ceiling the deployment accepted with one chosen after the fact,
            # which is the widening an attribute write is refused for; the
            # accepted record stays, and the base constructor never runs.
            raise ConfigurationError(
                "A schema is configured when it is constructed; re-running "
                "DjangoSchema.__init__ on one that is already serving requests "
                "would replace the policies it was accepted with. Construct a "
                "new schema instead.",
            )
        # Settled BEFORE the base constructor runs: that constructor's one
        # write to ``self.extensions`` is what settles the accepted extension
        # configuration, and the setter that takes it reads this record.
        _SCHEMA_ENFORCEMENT.settle(
            self,
            _SchemaEnforcement(
                resource_policy=resolved_resource,
                error_policy=resolved_error,
                auto_resource_extension=auto_resource,
                auto_error_extension=auto_error,
            ),
        )
        super().__init__(*args, **kwargs)

    @property
    def extensions(self) -> tuple[Any, ...]:
        """The extension configuration this schema was accepted with.

        Not read from an instance attribute, and for the reason the policies
        are not read from one either. ``strawberry.Schema.get_extensions`` builds every operation's
        extension list out of this, and ``info.schema`` puts it in reach of
        every resolver: as an ordinary attribute it is the seam that decides
        what enforces the NEXT request. Assigning a list carrying a
        ``DjangoResourcePolicyExtension`` with a wider policy of its own
        nominates a new enforcement authority, and assigning an empty one leaves
        a bounded schema running with no budget and no masking at all - either
        one for the life of the process, not for the operation that did it.
        Deduplication and presence checks cannot tell those lists apart from a
        configured one, because by then they are the configuration.

        Reading is unchanged, and answers with the entries construction
        accepted rather than with whatever the attribute holding them carries
        now: writing entries into it does not make them this schema's
        configuration. What such a write can do is drop the last hold on an
        accepted entry, and a configuration with an entry missing reads as the
        empty one, for :meth:`get_extensions` to refuse the operation on rather
        than run it.
        """
        accepted = _SCHEMA_EXTENSIONS.recall(self)
        return () if accepted is None else accepted

    @extensions.setter
    def extensions(self, value: Any) -> None:
        """Settle the accepted configuration, once, from the base constructor.

        ``strawberry.Schema.__init__`` materializes its ``extensions=`` argument
        into this attribute, and that write is the one that settles it. Every
        later write is refused rather than ignored: a consumer composing
        extensions after construction is making a configuration statement this
        schema cannot act on, and saying so is the difference between a
        deployment that fixes it and one that believes it took effect.
        """
        record = _enforcement(self)
        if record.extensions_settled:
            raise ConfigurationError(
                "A schema's extensions are settled when the schema is constructed; "
                "assigning schema.extensions afterwards would let what enforces an "
                "operation be chosen after the schema was accepted. Pass every "
                "extension to DjangoSchema(extensions=[...]).",
            )
        # The flag goes where no attribute answers with it, so that deleting the
        # accepted entries cannot make a schema look unconstructed and admit a
        # replacement list as its first settlement.
        _SCHEMA_ENFORCEMENT.settle(self, replace(record, extensions_settled=True))
        try:
            _SCHEMA_EXTENSIONS.accept(self, value)
        except TypeError as exc:
            # Each accepted entry is answered for by a weak reference to it, so
            # an entry that takes none is one no later operation could resolve
            # as the configuration rather than as whatever replaced it. Every
            # extension Strawberry accepts - a class, an instance, a factory -
            # takes one; refusing here names the entry that does not, at the
            # construction that supplied it.
            raise ConfigurationError(
                "Every entry in DjangoSchema(extensions=[...]) has to be an object the "
                "schema can hold as accepted - a SchemaExtension subclass, an instance "
                f"of one, or a callable returning one. {value!r} contains an entry that "
                "cannot be held.",
            ) from exc

    @property
    def resource_policy(self) -> ResourcePolicy:
        """The resolved execution resource policy, as a copy per read.

        The resolved policy is the authority every bound in the request is read
        from, and ``info.schema`` puts this attribute in reach of every resolver
        in every operation. Handing out the authority itself would make the
        attribute a write seam onto it - a frozen dataclass still admits
        ``policy.__dict__[bound] = wider``, and the object is process-lived, so
        one such write would widen every later request on the process and not
        just the one that made it. Each read therefore answers with a duplicate
        (``utils/policies.py::copy_policy``): reading a bound is unchanged,
        writing one changes only the reader's own copy. The authority the copy
        is taken from is the accepted enforcement record, which no name on
        this object answers with, so REPLACING it is not reachable through
        ``info.schema`` either.
        """
        return copy_policy(_enforcement(self).resource_policy)

    @property
    def error_policy(self) -> ErrorPolicy:
        """The resolved error policy, as a copy per read.

        The same boundary as :attr:`resource_policy`, for the policy whose
        ``enabled`` decides whether an unexpected exception is masked at all:
        writing it on the stored object would turn masking off for every later
        request on the process and put the raw exception text on the wire, and
        so would replacing the attribute it was read from - which is why this
        one is held in the accepted enforcement record beside the resource
        policy rather than on the schema.
        """
        return copy_policy(_enforcement(self).error_policy)

    def get_extensions(self, sync: bool = False) -> list[Any]:
        """Resolve extensions and remove a duplicate automatic policy instance.

        Strawberry accepts classes, instances, and zero-argument factories. A
        factory cannot be identified by type without calling it, and calling it
        during schema construction would violate its fresh-per-operation
        lifecycle. When the constructor had to add an automatic policy class
        because the consumer supplied only opaque entries, runtime resolution is
        the first safe point to see whether one of those entries produced an
        explicit policy extension of that kind. If so, the automatic entry is
        removed and every consumer entry keeps its place and its order.

        BOTH policies are deduplicated here, on the same terms. A second
        resource-policy extension is not a cosmetic duplicate: each one arms its
        own budget over the whole operation, the last one armed is what
        ``resource_policy.py::policy_from_info`` and ``check_deadline`` answer
        with, and the automatic entry is appended AFTER the consumer's, so a
        consumer who configured a narrow policy through a factory would get the
        package defaults enforced at every resolve-time bound while their own
        policy still charged the document - a split authority whose looser half
        wins exactly where the rows are.

        Which resolved instance is the automatic one follows from where the
        constructor put it: the error-policy entry is PREPENDED, so it is the
        first of its kind, and the resource-policy entry is APPENDED, so it is
        the last.

        What comes back always ENFORCES, and nothing here has to put an
        enforcement entry back to make that true: the entries resolved are the
        ones :attr:`extensions` settled at construction, and the constructor put
        both of the package's own into that configuration. Deduplication decides
        only which of two policy extensions of a kind survives.

        The list ends with a package-owned guard rather than with a consumer
        entry. Upstream decides whether to execute from inside the validation
        stage, so the operation's published rejection has to survive the last
        validation hook to set up; appending answers for every consumer entry
        without moving any of them, which is what keeps a supported validation
        cache working wherever the consumer put it.

        A schema that DID settle a configuration and can no longer answer with
        it is the one case nothing is resolved for. An accepted entry is the
        only record of what that extension declared - a factory's policy was
        never seen by this package at all - so an entry that no longer exists
        leaves nothing to resolve in its place: falling back to this schema's
        own policy would answer a lost entry with a budget the deployment never
        chose, and the entries that replaced it are ones no construction
        accepted. The operation is refused instead.
        """
        enforcement = _enforcement(self)
        if enforcement.extensions_settled and _SCHEMA_EXTENSIONS.recall(self) is None:
            return [DjangoErrorPolicyExtension(), _RefusedConfiguration()]
        resolved = super().get_extensions(sync=sync)
        if enforcement.auto_error_extension:
            resolved = _without_automatic_policy(
                resolved,
                DjangoErrorPolicyExtension,
                automatic=0,
            )
        if enforcement.auto_resource_extension:
            resolved = _without_automatic_policy(
                resolved,
                DjangoResourcePolicyExtension,
                automatic=-1,
            )
        return [*resolved, _AdmissionGuard()]


def _is_extension(extension: Any, extension_type: type) -> bool:
    """Whether a RESOLVED entry is of ``extension_type``, by its type alone.

    ``isinstance`` consults ``__class__``, which a consumer object answers with
    whatever it likes - and this predicate decides which of two entries of a
    kind survives deduplication, so an object that merely claims to be one is an
    object that can take the surviving place from the entry actually enforcing
    the request. ``type()`` cannot be answered.
    """
    return issubclass(type(extension), extension_type)


def _without_automatic_policy(
    resolved: list[Any],
    extension_type: type,
    *,
    automatic: int,
) -> list[Any]:
    """Drop the automatic ``extension_type`` entry when a consumer entry resolved beside it.

    ``automatic`` is the position the constructor put its own entry at among the
    resolved extensions of this type - ``0`` for a prepended one, ``-1`` for an
    appended one - which is the only thing that distinguishes it from the
    consumer's, both being ordinary instances by the time Strawberry has called
    every factory. With one or none of a kind there is nothing to choose between
    and the list is returned untouched.
    """
    indexes = [
        index
        for index, extension in enumerate(resolved)
        if _is_extension(extension, extension_type)
    ]
    if len(indexes) <= 1:
        return resolved
    dropped = indexes[automatic]
    return [extension for index, extension in enumerate(resolved) if index != dropped]


def _with_resource_policy_extension(extensions: Any) -> tuple[list[Any], bool]:
    """Return ``extensions`` with the resource-policy extension appended if absent.

    The extension is appended as a CLASS, which is what Strawberry wants: it
    constructs one instance per request, so a class (or factory) is what gives
    each operation its own charge counters. Passing an instance would share one
    set of counters across every concurrent request on the process.

    A consumer-supplied entry - class or instance - suppresses the append, so a
    consumer who installed the extension with a policy of their own keeps exactly
    that entry rather than getting a second copy whose charges would double-count
    against the same bounds. A consumer who wants a different policy without
    touching ``extensions`` passes ``DjangoSchema(resource_policy=...)``, which is
    the supported spelling.

    A bare factory callable (``lambda: DjangoResourcePolicyExtension(...)``) is
    opaque to this check by construction - identifying it would mean calling it
    at schema construction, which is the one thing a per-operation factory must
    not have done to it - so the append happens and the second flag this returns
    says so. ``DjangoSchema.get_extensions`` is where that is settled, at the
    first point a resolved instance can be seen.
    """
    # Do not use truthiness to normalize the consumer's iterable.  A list
    # subclass can override ``__bool__`` (or be stateful), and extension
    # installation must not invoke that arbitrary hook before Strawberry sees
    # the actual entries.  ``None`` is the only omitted-value spelling.
    installed = [] if extensions is None else list(extensions)
    for extension in installed:
        if _extension_entry_matches(extension, DjangoResourcePolicyExtension):
            return installed, False
    installed.append(DjangoResourcePolicyExtension)
    return installed, True


def _with_error_policy_extension(extensions: list[Any]) -> list[Any]:
    """Return ``extensions`` with the error-policy extension PREPENDED if absent.

    Prepended, not appended, and the position is the contract (spec-048
    Decision 10). Strawberry's ``on_operation`` teardowns unwind LIFO, so the
    first-listed extension tears down LAST - and masking must be last, after
    every extension that reads ``GraphQLError.original_error`` has had its turn.
    ``extensions/debug.py::DjangoDebugExtension`` is exactly such an extension
    and is documented to be listed after any masking extension; appending here
    would silently empty its ``exceptions`` list on any schema that installs
    both. The resource-policy extension appends for the mirror-image reason: it
    gates BEFORE execution, so it wants to set up last.

    A consumer-supplied entry - class or instance - suppresses the prepend, so a
    consumer who installed the extension at a position of their own keeps
    exactly that entry rather than getting a second copy that would mask an
    already-masked error and mint a second correlation id for it.
    """
    for extension in extensions:
        if _extension_entry_matches(extension, DjangoErrorPolicyExtension):
            return extensions
    return [DjangoErrorPolicyExtension, *extensions]


def _extension_entry_matches(extension: Any, extension_type: type) -> bool:
    """Match a class or instance entry without invoking opaque factories."""
    try:
        candidate = extension if isinstance(extension, type) else type(extension)
        return issubclass(candidate, extension_type)
    except Exception:
        return False
