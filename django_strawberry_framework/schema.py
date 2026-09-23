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
from graphql import GraphQLError, parse
from graphql.execution.execute import ExecutionContext
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types.graphql import OperationType

from . import logger
from .error_policy import _PACKAGE_ERROR_POLICY, ErrorPolicy, resolve_error_policy
from .exceptions import ConfigurationError, describe_value
from .extensions.error_policy import (
    DjangoErrorPolicyExtension,
    degraded_result,
    is_maskable_result,
    mask_execution_result,
    masking_is_active,
)
from .extensions.operation_state import DjangoExtensionsRunner, _OperationModeMarker
from .extensions.resource_policy import DjangoResourcePolicyExtension, _AdmissionGuard
from .mutations.fields import MUTATION_CLASS_MARKER
from .resource_policy import _PACKAGE_RESOURCE_POLICY, ResourcePolicy, resolve_resource_policy
from .utils.execution_mode import OperationMode, async_execution
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
        if async_execution():
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

    The two resolved policies - which is the whole of what enforces an
    operation on this schema - and whether the base constructor has settled the
    extension configuration yet. Every field is a policy of primitives or a
    flag, so the record points at nothing: it can be held for the schema
    without keeping the schema alive.

    **The enforcement extensions are built from this record and from nothing
    else.** They are not entries in the configuration a consumer supplies, so
    no object a consumer can still reach decides what the next operation is
    bounded by or whether its unexpected exceptions are masked. Accepting an
    entry proves which object a schema was configured with; it cannot prove
    what that object will DO on the operation after this one, and a factory is
    consumer code that may answer differently every time it is called.
    """

    resource_policy: ResourcePolicy
    error_policy: ErrorPolicy
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
#: ``utils/private_state.py::PrivateMembership`` holds one piece of weak evidence
#: per accepted ENTRY - which is the granularity the question is asked at. What
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
#: bound its requests and the masking error policy applies. This is not a
#: fallback for a configuration that was tampered with: a settled record cannot
#: go missing while its schema is alive.
_FALLBACK_ENFORCEMENT = _SchemaEnforcement(
    resource_policy=_PACKAGE_RESOURCE_POLICY,
    error_policy=_PACKAGE_ERROR_POLICY,
)


def _enforcement(schema: Any) -> _SchemaEnforcement:
    """The record ``schema`` was settled with, or the record of one that settled none."""
    record = _SCHEMA_ENFORCEMENT.recall(schema)
    return _FALLBACK_ENFORCEMENT if record is None else record


#: What the wire is told when a schema cannot produce the chain it was accepted
#: with. One message per cause and nothing more: the object that was invalid,
#: the exception a factory raised, and the population that was ambiguous are all
#: diagnostics for the deployment's own logs, and a wire field carrying any of
#: them hands a client the shape of a schema's configuration.
_UNREADABLE_CONFIGURATION = (
    "The schema's accepted extension configuration could not be read back, "
    "so the operation cannot be enforced as configured."
)
_UNRESOLVED_CHAIN = (
    "The schema's extensions did not resolve into the enforcement configuration "
    "the schema was accepted with, so the operation cannot be enforced as configured."
)


#: The document a refused operation is given in place of the one that arrived,
#: one per operation type. Each is anonymous and parsed once, at import: the
#: refusal runs no parser on a request, and an operation type the caller did not
#: allow is refused by upstream before it can read the refusal, so the type is
#: chosen from what the transport allows - a subscription transport allows
#: exactly one. Nothing validates or executes them, so one object answers every
#: refused request of its type.
_REFUSAL_DOCUMENTS = {
    OperationType.QUERY: parse("query { __typename }"),
    OperationType.MUTATION: parse("mutation { __typename }"),
    OperationType.SUBSCRIPTION: parse("subscription { __typename }"),
}


def _refuse_operation_document(execution_context: Any) -> None:
    """Give the parse stage the package's own document, selected by nothing.

    A refused schema runs nothing, and that has to include the parser: a
    document is arbitrary-length consumer input and graphql-core parses it
    recursively, so a deployment whose extension configuration broke would
    otherwise answer every request with a refusal while still lexing and
    nesting whatever was sent to it - the one shape where a broken deployment
    would be more exposed than a working one.

    The document and the operation selector are replaced together. Upstream
    picks the operation to run by looking the REQUESTED name up in whatever
    document the parse stage left behind, and raises when it cannot find it, so
    a substitute document reached by a name still belonging to the request is a
    second error over the published refusal - raised out of the synchronous API,
    and in place of the refusal frame on a stream. Once the request's document
    has been discarded its operation name selects nothing: the substitute
    carries a single anonymous operation, and the selector is the package's own
    ``None``.

    The request's own text and name stay on the execution context as request
    diagnostics for whatever transport wants to log them. Neither takes part in
    parsing, selection, validation or execution again.

    The transport policy is snapshotted before it is read, because reading it
    twice is not the same as reading it once. ``allowed_operation_types`` is
    annotated ``Iterable[OperationType]`` on all three public entry points, and
    upstream tests the operation it settled on against whatever object the
    caller passed - once, after parsing. A one-shot iterable is a valid value
    for that annotation and a healthy operation consumes it exactly once, so a
    refusal that searched the caller's object for a substitute document would
    hand upstream an exhausted one and turn a policy that allows this operation
    into one that forbids it. Nor is the object asked whether it is empty: that
    is a consumer-defined ``__bool__`` on the request path of a schema whose
    configuration is already known to be broken, and every other read of a
    consumer container here refuses truthiness for the same reason.

    So the policy is materialized ONCE into an exact built-in tuple, that tuple
    is put back on the execution context, and package selection and upstream
    authorization then read one immutable fact. A policy that genuinely allows
    nothing stays a policy that allows nothing - upstream refuses the operation
    type it would have refused anyway, which is the transport's answer to give.
    """
    # One read, no truthiness, and the snapshot is what upstream reads back.
    allowed = tuple(execution_context.allowed_operations)
    execution_context.allowed_operations = allowed
    execution_context.graphql_document = next(
        (
            document
            for operation_type, document in _REFUSAL_DOCUMENTS.items()
            if operation_type in allowed
        ),
        _REFUSAL_DOCUMENTS[OperationType.QUERY],
    )
    # ``ExecutionContext.operation_name`` is a read-only property over the name
    # the request provided, falling back to the first operation in the document
    # once there is one. Clearing the provided name is what makes the fallback -
    # the package's own anonymous operation - the answer.
    execution_context._provided_operation_name = None


class _RefusedConfiguration(SchemaExtension):
    """Refuse every operation on a schema that cannot produce its accepted chain.

    Installed in place of the consumer chain in two cases. The configuration a
    schema was constructed with was replaced or deleted behind the attribute
    holding it; or the accepted entries no longer resolve into that
    configuration - a factory raised, or returned something that is not a
    ``SchemaExtension`` instance or that claims an enforcement authority the
    package owns. Running the operation anyway would mean enforcing something
    other than what the deployment accepted, and in the first case the entries
    that are missing are the only record of what they declared.

    The refusal is PUBLISHED as this request's pre-execution error and restated
    where execution would begin, which is the pair of seams every transport
    renders - the same shape a resource rejection uses, for the same reason: an
    exception out of a hook leaves a streaming operation with no frame at all.

    It is published BEFORE the document is parsed, and the parse stage is given
    a document of the package's own so the document that arrived never reaches a
    parser (:func:`_refuse_operation_document`). Publishing after the parse
    would make the refusal true only of documents that happen to be well formed:
    a syntax error is raised out of the parse itself, and upstream answers with
    it before any statement after this hook's ``yield`` has run. It is restated
    after the ``yield`` as well, so a consumer parse hook the package still
    cannot see cannot leave something else published.
    """

    def __init__(self, message: str) -> None:
        self._message = message

    def on_parse(self) -> Iterator[None]:
        """Answer the parse stage with the refusal instead of the document sent."""
        execution_context = self.execution_context
        _refuse_operation_document(execution_context)
        execution_context.validation_rules = ()
        execution_context.pre_execution_errors = [self._refusal()]
        yield
        execution_context.validation_rules = ()
        execution_context.pre_execution_errors = [self._refusal()]

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
            self._message,
            extensions={"code": SCHEMA_CONFIGURATION_ERROR_CODE},
        )


def _refused_chain(message: str, reason: str, *, sync: bool) -> list[Any]:
    """The only chain a refused configuration runs: mask, refuse, and still bound.

    Both package authorities are kept. The masking extension is kept because the
    refusal still travels as an ordinary response and an unexpected exception
    from anything upstream of it must not reach the client raw. The resource
    extension is kept because a refusal published at the parse stage is a
    statement about a document that already arrived: its pre-parse token and
    depth scan is the only thing standing between an unauthenticated caller and
    graphql-core's recursive parser, and a deployment whose extension
    configuration broke would otherwise have traded "every operation fails
    closed" for an endpoint with no ceiling on what it accepts. Both are built
    from this schema's own record (:class:`_SchemaEnforcement`), which is the
    one configuration still known to be the accepted one.

    Nothing else runs - no consumer hook, no resolver - because what a consumer
    entry would enforce is exactly what could not be established.

    The refusal sits between them so that the parse stage's LAST word is the
    configuration code: hooks tear down in reverse, so a document charge that
    rejects the package's own substitute document cannot answer for a request
    the schema is refusing outright.

    ``reason`` names the object or the population that failed, for the
    deployment's own logs. It never reaches ``message``: a factory's exception
    text and a bad member's representation are the consumer's own strings, and
    the wire gets the stable code instead.

    The operation's executor mode is declared here too, behind both
    authorities. A refused operation still runs this schema's own extensions,
    and what they may hand back depends on which executor is driving exactly as
    it does for an admitted one - so the fact travels on the refusal path as
    well, rather than being the one chain where a field falls back to guessing.
    """
    logger.error("Refusing every operation on this schema: %s", reason)
    return [
        DjangoErrorPolicyExtension(),
        _RefusedConfiguration(message),
        DjangoResourcePolicyExtension(),
        _OperationModeMarker(_operation_mode(sync=sync)),
    ]


def _operation_mode(*, sync: bool) -> OperationMode:
    """The executor this operation is being driven by, from the flag upstream passed.

    ``get_extensions(sync=True)`` is ``execute_sync`` and nothing else;
    ``execute``, ``stream`` and ``subscribe`` all leave it false. That flag is
    the authoritative statement of which executor holds the operation, and it is
    the only one: the ambient event loop answers a different question and
    disagrees with this one whenever a synchronous operation is started from
    inside an asynchronous one.
    """
    return OperationMode.SYNC if sync else OperationMode.ASYNC


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
    ``extensions/resource_policy.py::DjangoResourcePolicyExtension``, which every
    operation's chain begins and ends with whatever the consumer configured. A
    schema built through this class is therefore bounded with no opt-in
    boilerplate, which is the whole point: an endpoint whose only limiter is one
    a consumer remembered to install is an endpoint with no limiter.

    **The production error policy is resolved here too, and by the same rule.**
    ``error_policy=`` accepts an ``ErrorPolicy`` or a mapping of option names to
    values; omitted, the ``DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]`` setting
    and then the package defaults apply. It is validated at construction, exposed
    as ``schema.error_policy``, and enforced by
    ``extensions/error_policy.py::DjangoErrorPolicyExtension``, which is FIRST in
    every operation's chain - the position is load-bearing, see
    ``_admitted_chain``. Under ``settings.DEBUG = False`` an unexpected resolver
    or hook exception therefore reaches the client as a stable message plus a
    correlation identifier rather than as whatever the exception happened to say.
    Opting out is explicit: ``DjangoSchema(error_policy={"enabled": False})``.

    **An exception that escapes a HOOK is masked by this class rather than by
    that extension**, because upstream converts such an exception into a result
    only after every teardown has unwound, and nothing an extension can hook runs
    afterwards. :meth:`_masked_return` is that seam, applied to what
    :meth:`execute` and :meth:`execute_sync` hand back; it shares the extension's
    one masking implementation and is a no-op on a result the teardown already
    masked. A consumer assembling a plain ``strawberry.Schema`` around the
    exported extension has no such seam, so a hook failure is unmasked there.

    **Both authorities are the schema's, not entries in ``extensions=``.** They
    are built per operation from the record this constructor settles, so
    ``extensions=`` carries the consumer's own extensions and nothing else, and
    the two arguments above are the only way to configure what enforces a
    request. Supplying ``DjangoResourcePolicyExtension(policy=...)`` as an entry
    still works and is read as a declaration of that policy - the entry is
    folded into the record rather than kept - and declaring the policy twice is
    refused here, as is a subclass of either enforcement extension -
    supplied as a class or as an instance, and whether or not it declares a
    policy of its own - because a subclass can override the hook that does the
    enforcing while still answering every check for it. An entry that would
    decide enforcement later, rather than at the construction that accepted it,
    is refused when the operation resolves it (:meth:`get_extensions`): a
    factory is consumer code, and what it returns next request is not something
    accepting it this request can answer for.
    """

    def __init__(
        self,
        *args: Any,
        resource_policy: ResourcePolicy | Mapping[str, Any] | None = None,
        error_policy: ErrorPolicy | Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        entries, declared_resource = _consumer_extension_entries(kwargs.get("extensions"))
        if declared_resource is not None and resource_policy is not None:
            raise ConfigurationError(
                "A schema's resource policy is declared once. This one is declared "
                "twice - by DjangoSchema(resource_policy=...) and by a "
                "DjangoResourcePolicyExtension(policy=...) entry - and the two "
                "declarations are not composable into one ceiling. Keep the "
                "resource_policy= argument.",
            )
        resolved_resource = resolve_resource_policy(
            resource_policy if declared_resource is None else declared_resource,
        )
        resolved_error = resolve_error_policy(error_policy)
        if kwargs.get("execution_context_class") is None:
            kwargs["execution_context_class"] = DjangoMutationExecutionContext
        kwargs["extensions"] = entries
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
            ),
        )
        super().__init__(*args, **kwargs)

    @property
    def extensions(self) -> tuple[Any, ...]:
        """The CONSUMER extension configuration this schema was accepted with.

        The package's own enforcement extensions are not in it and never were
        an entry: they are built per operation from the accepted record
        (:func:`_admitted_chain`), so an operation is bounded and masked whatever
        this answers with.

        What it does decide is which consumer extensions run, and it is not read
        from an instance attribute for the reason the policies are not read from
        one either. ``strawberry.Schema.get_extensions`` builds every operation's
        extension list out of this, and ``info.schema`` puts it in reach of every
        resolver: as an ordinary attribute it is the seam that decides what runs
        in the NEXT request, and a write to it is for the life of the process
        rather than for the operation that did it.

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
        # Refused per ENTRY, before anything is settled, and refused for exactly
        # one reason: Strawberry could not resolve it into an extension for an
        # operation. Its own resolution is ``ext if isinstance(ext,
        # SchemaExtension) else ext()``, so a class, an instance and a callable
        # are the three shapes; anything else fails at the first operation, deep
        # inside the engine, on a schema the deployment already started. Naming
        # it at the construction that supplied it is the same failure one
        # startup earlier.
        #
        # A memory layout is NOT one of the reasons. A callable factory with
        # ``__slots__ = ()`` takes no weak reference and runs perfectly well,
        # and how such an entry is answered for is this package's problem to
        # solve (``utils/private_state.py::PrivateMembership``) rather than a
        # configuration the consumer has to respell.
        for entry in value:
            if not _is_resolvable_extension_entry(entry):
                raise ConfigurationError(
                    "Every entry in DjangoSchema(extensions=[...]) has to be something "
                    "Strawberry can resolve into an extension for an operation - a "
                    "SchemaExtension subclass, an instance of one, or a callable that "
                    f"returns one. {describe_value(entry)} is none of those.",
                )
        # The flag goes where no attribute answers with it, so that deleting the
        # accepted entries cannot make a schema look unconstructed and admit a
        # replacement list as its first settlement.
        _SCHEMA_ENFORCEMENT.settle(self, replace(record, extensions_settled=True))
        _SCHEMA_EXTENSIONS.accept(self, value)

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
        """Resolve the accepted entries into this operation's chain, or refuse it.

        The chain is this schema's two enforcement authorities with the
        consumer's resolved extensions between them. Both authorities are built
        here, from the private record this schema was constructed with
        (:class:`_SchemaEnforcement`), and neither is an entry a consumer
        supplied: the error policy tears down last, so it is first, and the
        resource policy sets up last, so it is last but for the guard behind it.

        **An enforcement authority is not something an extension entry can
        claim.** An accepted entry proves which object this schema was
        configured with, and for an inert extension that is the whole question.
        For the two authorities it is not: a factory is consumer code, it is
        handed back to every resolver through ``info.schema.extensions``, and
        what it returns on the NEXT operation is decided after this one. A
        stateful factory widened by a resolver, a closure over a mutable cell, a
        singleton selector that changes which object it hands out, and a
        subclass overriding the one hook that masks or charges are all the same
        defect, and identity evidence about the entry answers none of them. So
        the configuration seams are ``resource_policy=`` and ``error_policy=``,
        which canonicalize into a record of primitives at construction, and a
        resolved member claiming either role is refused rather than admitted.

        Strawberry accepts classes, instances, and zero-argument factories, and
        every one of those remains supported for an ordinary consumer extension
        - the optimizer's documented singleton-in-a-factory included. A factory
        cannot be identified by type without calling it, and calling it during
        schema construction would violate its fresh-per-operation lifecycle, so
        what a factory PRODUCES can only be admitted here.

        **Resolution is that admission boundary**, and it is one transaction:
        calling the factories, typing what they returned, and checking what
        those members claim all happen here, before any of it reaches
        Strawberry. Construction can answer for the entries themselves and
        nothing more, so this is where the other half is settled:

        - A factory that RAISES is refused rather than allowed to escape. It
          escapes from here, which is outside the block upstream converts into a
          response, so what a consumer's exception says would reach the client
          unmasked and the package's own error policy would never see it.
        - A member that is not a ``SchemaExtension`` INSTANCE is refused. A
          class is not one either: upstream resolves an entry once and assigns
          ``execution_context`` on whatever came back, so an integer, a bare
          object or a class produces an ``AttributeError`` deep in the engine,
          again outside every seam this package masks or refuses at.
        - A member of either enforcement kind is refused, subclasses included.
          One class can inherit from both, in which case ordinary method
          resolution runs one of two colliding hooks and the other authority is
          present in name only; and a single-role subclass can override the hook
          that does the work while answering every inheritance check correctly.
          Neither is a configuration a deployment can have meant, and neither is
          distinguishable from the real thing by anything but exact type.

        A schema that DID settle a configuration and can no longer answer with
        it is the one case nothing is resolved for. An accepted entry is the
        only record of what that extension declared, so an entry that no longer
        exists leaves nothing to resolve in its place and the operation is
        refused instead.

        Nothing is resolved twice to establish any of it: the factories run
        once, through upstream, and every check reads the members that came
        back.
        """
        enforcement = _enforcement(self)
        if enforcement.extensions_settled and _SCHEMA_EXTENSIONS.recall(self) is None:
            return _refused_chain(
                _UNREADABLE_CONFIGURATION,
                "the accepted extension entries can no longer be read back",
                sync=sync,
            )
        try:
            resolved = super().get_extensions(sync=sync)
        except Exception as exc:
            # ``describe_value`` and not ``{exc!r}``: the object being rendered
            # is a consumer exception raised by a consumer factory, and its
            # ``__repr__`` is as much consumer code as the factory was. An
            # f-string here would let it raise while the containment result is
            # being built, replacing the refusal with the very exception the
            # refusal exists to keep off the wire.
            return _refused_chain(
                _UNRESOLVED_CHAIN,
                f"resolving the accepted extension entries raised {describe_value(exc)}",
                sync=sync,
            )
        for member in resolved:
            if not _is_extension(member, SchemaExtension):
                return _refused_chain(
                    _UNRESOLVED_CHAIN,
                    f"a resolved extension entry is {describe_value(member)}, "
                    "which is not a SchemaExtension instance",
                    sync=sync,
                )
            claimed = _claimed_authority(member)
            if claimed is not None:
                return _refused_chain(
                    _UNRESOLVED_CHAIN,
                    f"a resolved extension entry is {describe_value(member)}, "
                    f"which claims the {claimed} authority this schema owns",
                    sync=sync,
                )
        return _admitted_chain(resolved, sync=sync)

    def create_extensions_runner(
        self,
        execution_context: Any,
        extensions: list[Any],
    ) -> DjangoExtensionsRunner:
        """Build the runner that owns every framework extension's operation state.

        The one point that sees the resolved extension list and this operation's
        engine context together, after upstream's assignment loop and without
        calling a factory a second time - which is why the boundary is here and
        not in each extension's hooks. A class entry, an accepted instance and a
        factory returning a shared singleton all arrive as resolved members, and
        all three get one state per operation out of this.

        The context handed here is the whole input: upstream assigns
        ``execution_context`` on every resolved extension just before this call
        and runs no hook in between, so the assignment carries nothing this
        argument does not, and recording it would only add a place for a
        half-built request to be left behind.
        """
        return DjangoExtensionsRunner(
            execution_context=execution_context,
            extensions=extensions,
        )

    def execute_sync(self, *args: Any, **kwargs: Any) -> Any:
        """Run the operation synchronously and mask what is RETURNED.

        The masking extension's teardown answers for a result upstream assigned
        to the execution context, and for the ordinary operation that is the same
        object this returns. It is not the same object when an exception escaped
        a hook: upstream converts that exception into a fresh result inside the
        ``except`` behind its operation lifecycle, which runs after every teardown
        has already unwound over an execution context whose ``result`` was still
        ``None``. No extension can reach that result, because none is still
        running when it is built - so the schema masks the value it hands back.
        """
        return self._masked_return(super().execute_sync(*args, **kwargs))

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Run the operation asynchronously and mask what is RETURNED.

        The async twin of :meth:`execute_sync`, for the same reason and with the
        same one hole to close: upstream's own ``except`` hands the coerced
        exception to a handler that assigns ``execution_context.result`` only
        AFTER the operation lifecycle has finished unwinding, so the teardown saw
        nothing and the leak is identical. Streamed operations are not masked
        here - each frame is masked at the transport's result source - and
        nothing about this override touches them.
        """
        return self._masked_return(await super().execute(*args, **kwargs))

    def _masked_return(self, result: Any) -> Any:
        """Apply this schema's error policy to one returned execution result.

        The gates and the masking itself are the extension module's own
        (``extensions/error_policy.py``), so this seam cannot drift from the
        operation teardown or the streamed-result source on what counts as
        active, what shape is maskable, or what a masked error looks like. The
        policy is read from the accepted enforcement record rather than from
        ``schema.error_policy``, which answers with a per-read copy any resolver
        can reach.

        **Masking twice is a no-op, by construction rather than by a flag.** A
        result the teardown already masked carries errors whose ``original_error``
        is ``None``, and the structural classifier reads that as a deliberate,
        client-facing error and returns it unchanged - so the whole error list
        comes back identical, ``mask_execution_result`` answers with the very
        object it was handed, and no second correlation id is minted or logged.
        Nothing here needs to know whether the teardown ran.

        **It fails closed**, exactly as the teardown does: a seam that cannot
        decide whether to mask publishes the policy message alone rather than
        whatever the result was carrying. ``mask_execution_result`` already
        contains its own failures, so what is left for this guard is a policy
        record or a gate that will not answer at all. The floor is built from the
        package default until the schema's own policy has been read, because the
        read is inside what is guarded and a degrade that had to read it again to
        publish its message would be a floor that can raise.
        """
        policy = _PACKAGE_ERROR_POLICY
        try:
            policy = _enforcement(self).error_policy
            if not masking_is_active(policy) or not is_maskable_result(result):
                return result
            return mask_execution_result(result, policy)
        except Exception:
            logger.exception(
                "The error policy could not be applied to the returned execution result; "
                "the response degrades to the policy message alone (fail closed).",
            )
            return degraded_result(policy)

    def _stream(
        self,
        execution_context: Any,
        extensions_runner: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Stream the operation's frames with this operation bound in every task.

        The narrowest seam that already receives the exact runner and the raw
        iterator upstream built, which is what the wrapper needs: a streamed
        operation's frames are produced wherever the transport drives them, and
        an async generator's body runs in the resuming caller's context. Upstream
        binds nothing per resume because nothing upstream is task-local; this
        package's budget, operation state and optimizer frame all are.

        ``stream`` and ``subscribe`` both come through here - the second is a
        thin wrapper around the first - so one override covers every streamed
        operation on every transport. A runner some subclass built instead is
        passed through untouched: the wrapper binds what a
        :class:`DjangoExtensionsRunner` owns and has nothing to say about
        anything else.
        """
        source = super()._stream(execution_context, extensions_runner, *args, **kwargs)
        if issubclass(type(extensions_runner), DjangoExtensionsRunner):
            return extensions_runner.resumed_stream(source)
        return source


def _is_resolvable_extension_entry(entry: Any) -> bool:
    """Whether Strawberry can turn ``entry`` into an extension for an operation.

    Its resolution is ``entry if isinstance(entry, SchemaExtension) else
    entry()``, so an instance answers for itself and everything else has to be
    callable - which a class and a factory both are. ``type()`` rather than
    ``isinstance`` for the reason :func:`_is_extension` uses it: a consumer
    object answers ``__class__`` with whatever it likes, and an object that only
    CLAIMS to be an extension must still pass as a callable to be accepted.
    """
    return issubclass(type(entry), SchemaExtension) or callable(entry)


def _is_extension(extension: Any, extension_type: type) -> bool:
    """Whether a RESOLVED entry is of ``extension_type``, by its type alone.

    ``isinstance`` consults ``__class__``, which a consumer object answers with
    whatever it likes. This predicate decides both whether a resolved member is
    an extension at all and whether it is a second enforcement authority, so a
    member whose ``__class__`` claims ``SchemaExtension`` would be handed to
    upstream as one, and a member claiming an ordinary class would be admitted
    beside the authority actually enforcing the request. ``type()`` cannot be
    answered.
    """
    return issubclass(type(extension), extension_type)


def _claimed_authority(member: Any) -> str | None:
    """Name the enforcement role a RESOLVED member claims, or ``None`` for an ordinary one.

    Both roles are checked and the first match is named, so one class inheriting
    from both is reported rather than counted twice. What is refused is the
    claim itself: this schema builds its own authority of each kind, so a
    resolved member of either kind is a second one whichever way it got there.
    """
    for extension_type, kind in (
        (DjangoResourcePolicyExtension, "resource-policy"),
        (DjangoErrorPolicyExtension, "error-policy"),
    ):
        if _is_extension(member, extension_type):
            return kind
    return None


def _admitted_chain(resolved: list[Any], *, sync: bool) -> list[Any]:
    """This schema's authorities around ``resolved``, and the guard behind them.

    The error policy is FIRST and the resource policy LAST, and both positions
    are the contract (spec-048 Decision 10). Strawberry's ``on_operation``
    teardowns unwind LIFO, so the first-listed extension tears down last - and
    masking must be last, after every extension that reads
    ``GraphQLError.original_error`` has had its turn.
    ``extensions/debug.py::DjangoDebugExtension`` is exactly such an extension
    and is documented to be listed after any masking extension. The resource
    policy is last for the mirror-image reason: it gates BEFORE execution, so it
    wants to set up last, with its own budget armed around every consumer hook.

    The guard goes behind every consumer entry because upstream decides whether
    to execute from inside the validation stage, so the operation's published
    rejection has to survive the last validation hook to set up; appending
    answers for every consumer entry without moving any of them, which is what
    keeps a supported validation cache working wherever the consumer put it.

    Both authorities are constructed fresh per operation and read their
    configuration from this schema, which answers from the private record. An
    instance shared across operations would share one set of charge counters
    between concurrent requests.

    The mode marker goes behind the guard because it is not a hook at all: it
    declares which executor is driving this operation, the runner reads it out
    of this list, and nothing in the chain's setup or teardown order has
    anything to say about it (``utils/execution_mode.py``).
    """
    return [
        DjangoErrorPolicyExtension(),
        *resolved,
        DjangoResourcePolicyExtension(),
        _AdmissionGuard(),
        _OperationModeMarker(_operation_mode(sync=sync)),
    ]


def _consumer_extension_entries(extensions: Any) -> tuple[list[Any], ResourcePolicy | None]:
    """Split ``extensions`` into the consumer's entries and the policy one of them declared.

    An enforcement extension supplied directly is a CONFIGURATION statement
    rather than a chain member: the schema installs its own of each kind on
    every operation, so keeping the entry too would put two of a kind in the
    chain, and keeping it INSTEAD would make the object a resolver can reach
    through ``info.schema.extensions`` the authority for every later request.
    So a directly supplied entry is read once, here, where it is being accepted,
    and what it declared is folded into the schema's record; the entry itself
    does not travel.

    Only an EXACT entry can be read that way. A subclass is refused, and refused
    at construction where it is actionable: its overrides are consumer code on
    the one hook that charges a document or masks a result, and an override that
    does nothing passes every check an inheritance census can make. Policy
    customization has a seam that is not behavior -
    ``DjangoSchema(resource_policy=...)`` and ``error_policy=`` - while an
    unrelated consumer extension remains free to implement any hook it likes.

    A bare class entry declares nothing beyond the automatic one and is simply
    dropped; an instance declares whatever policy it was constructed with.
    ``None`` comes back when no entry declared one, which is the ordinary case.
    """
    # Do not use truthiness to normalize the consumer's iterable.  A list
    # subclass can override ``__bool__`` (or be stateful), and extension
    # installation must not invoke that arbitrary hook before Strawberry sees
    # the actual entries.  ``None`` is the only omitted-value spelling.
    supplied = [] if extensions is None else list(extensions)
    entries: list[Any] = []
    declared: ResourcePolicy | None = None
    for entry in supplied:
        role = _declared_authority(entry)
        if role is None:
            entries.append(entry)
            continue
        if role is not DjangoResourcePolicyExtension:
            continue
        policy = _entry_resource_policy(entry)
        if policy is None:
            continue
        if declared is not None:
            raise ConfigurationError(
                "DjangoSchema(extensions=[...]) carries two resource-policy "
                "extensions declaring a policy of their own, and an operation is "
                "bounded by one. Declare it once, with "
                "DjangoSchema(resource_policy=...).",
            )
        declared = policy
    return entries, declared


def _declared_authority(entry: Any) -> type | None:
    """The enforcement kind ``entry`` declares directly, or ``None`` for any other entry.

    A class or an instance names its type without anything being run, which is
    what makes this answerable at construction; a factory is opaque until it is
    called and is left for :meth:`DjangoSchema.get_extensions`. A subclass of
    either kind never comes back as a declaration - it is refused here.
    """
    for extension_type, kind in (
        (DjangoResourcePolicyExtension, "resource-policy"),
        (DjangoErrorPolicyExtension, "error-policy"),
    ):
        if _entry_type(entry) is extension_type:
            return extension_type
        if _extension_entry_matches(entry, extension_type):
            raise ConfigurationError(
                f"{describe_value(entry)} subclasses the package's {kind} "
                "extension, and a schema's enforcement authority is not something "
                "an extension entry can be. A subclass can override the hook that "
                "does the enforcing while still answering every check for it. "
                "Configure the policy with DjangoSchema(resource_policy=...) or "
                "error_policy=, and give an unrelated extension its own hooks.",
            )
    return None


def _entry_resource_policy(entry: Any) -> ResourcePolicy | None:
    """The explicit policy a directly supplied resource-policy INSTANCE was built with.

    ``None`` for a class entry, which was never constructed and therefore
    declares nothing, and for an instance built without an override, which
    declares that it inherits its schema's policy. What comes back is the
    extension's own canonical copy, read through the private record that holds
    it rather than off the object.
    """
    if issubclass(type(entry), type):
        return None
    policy = entry._policy
    return policy if type(policy) is ResourcePolicy else None


def _entry_type(entry: Any) -> type:
    """The class an entry names - itself, or the type of the instance it is.

    Read with ``type()``, never ``isinstance``: a consumer instance answers
    ``__class__`` with whatever it likes, so one claiming to be a class would be
    classified as that claim, and an authority subclass claiming ``type`` would
    pass for an entry that declares nothing. ``type()`` cannot be answered and
    cannot raise.
    """
    return entry if issubclass(type(entry), type) else type(entry)


def _extension_entry_matches(extension: Any, extension_type: type) -> bool:
    """Match a class or instance entry by its real type, without invoking factories."""
    return issubclass(_entry_type(extension), extension_type)
