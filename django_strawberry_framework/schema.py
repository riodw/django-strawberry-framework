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
  thread and therefore one Django connection.

Mutation root fields execute serially (the GraphQL spec's mutation semantics,
graphql-core's ``execute_fields_serially``), so consecutive top-level mutation
fields get INDEPENDENT transactions: field two's transaction opens only after
field one's committed or rolled back.

Only fields whose resolver carries the ``DjangoMutationField`` marker are
wrapped; every other field (queries, consumer-written mutations, introspection)
executes exactly as stock graphql-core.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import strawberry
from django.db import transaction
from graphql.execution.execute import ExecutionContext
from strawberry.utils.inspect import in_async_context

from .error_policy import ErrorPolicy, resolve_error_policy
from .extensions.error_policy import DjangoErrorPolicyExtension
from .extensions.resource_policy import DjangoResourcePolicyExtension
from .mutations.fields import MUTATION_CLASS_MARKER
from .resource_policy import ResourcePolicy, resolve_resource_policy
from .utils.querysets import run_in_one_sync_boundary
from .utils.write_transaction import managed_write_transaction, resolve_write_alias


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

        alias = resolve_write_alias(mutation_cls._mutation_meta.model)
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
        if parent_type is not self.schema.mutation_type:
            return None
        field_def = parent_type.fields.get(field_nodes[0].name.value)
        if field_def is None:  # introspection (``__typename``) has no field entry here.
            return None
        strawberry_field = (field_def.extensions or {}).get("strawberry-definition")
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
            return collected.errors
        return self.errors

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
        calling thread. Any located error the execution collects during the
        window (a resolver error is a *located* error, not an exception, so an
        exception-based rollback would miss it) marks the transaction for
        rollback before the block exits.
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
        if len(self._execution_errors()) > errors_before:
            transaction.set_rollback(True, using=alias)
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
            if len(self._execution_errors()) > errors_before:
                transaction.set_rollback(True, using=alias)
            atomic.__exit__(None, None, None)

        await run_in_one_sync_boundary(_exit_clean)
        return result


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
        self.resource_policy = resolve_resource_policy(resource_policy)
        self.error_policy = resolve_error_policy(error_policy)
        kwargs.setdefault("execution_context_class", DjangoMutationExecutionContext)
        extensions = _with_resource_policy_extension(kwargs.get("extensions"))
        kwargs["extensions"] = _with_error_policy_extension(extensions)
        super().__init__(*args, **kwargs)


def _with_resource_policy_extension(extensions: Any) -> list[Any]:
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
    the supported spelling; a bare factory callable
    (``lambda: DjangoResourcePolicyExtension(...)``) is opaque to this check by
    construction, so a consumer using one should not also rely on suppression.
    """
    installed = list(extensions or [])
    for extension in installed:
        candidate = extension if isinstance(extension, type) else type(extension)
        if issubclass(candidate, DjangoResourcePolicyExtension):
            return installed
    installed.append(DjangoResourcePolicyExtension)
    return installed


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
        candidate = extension if isinstance(extension, type) else type(extension)
        if issubclass(candidate, DjangoErrorPolicyExtension):
            return extensions
    return [DjangoErrorPolicyExtension, *extensions]
