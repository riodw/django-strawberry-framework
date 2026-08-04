"""``DjangoErrorPolicyExtension`` - the response-side enforcement of ``ErrorPolicy``.

Spec: ``docs/SPECS/spec-048-secure_output_defaults-0_0_17.md``.
Target release: ``0.0.17``.

``error_policy.py`` owns the policy object; this module is the one place that
applies it. ``DjangoSchema`` installs the extension automatically, so a schema
built through this package does not leak an unexpected exception's message by
default.

One pass over a completed result: every error on it is classified and, when it is
unexpected, replaced by a fresh ``GraphQLError`` carrying the policy's stable
message and a correlation identifier, while the original exception is logged
server-side under that same identifier.

**There are two seams, because a response is not always one result.** A query or
mutation produces exactly one result, so this extension's ``on_operation``
teardown is the whole story for them. A SUBSCRIPTION delivers one
``ExecutionResult`` PER EVENT through the result source the transport iterates,
and that teardown runs only when the operation ENDS - so every event's errors
would already be on the wire by the time it ran. The per-event seam is therefore
the transport's own result source (``consumers.py::_stop_aware_results``), which
masks each yielded result through ``mask_execution_result`` below. One masking
implementation, two places it is applied, and neither re-states the
classification or the replacement.

``mask_execution_result`` RETURNS a masked value rather than editing the result
it was handed, which is what lets the per-event seam leave the engine's own
result object untouched: the extensions that read ``GraphQLError.original_error``
(``debug.py::DjangoDebugExtension`` above all) still see the originals on the
object the engine assigned to ``execution_context.result``, exactly as the LIFO
teardown ordering promises them.

**Install position is load-bearing, and it is the FRONT of the extensions
list.** Strawberry's ``on_operation`` teardowns unwind LIFO, so the
first-listed extension tears down LAST. Masking must happen after every
extension that reads ``original_error`` has had its turn - in particular
``debug.py::DjangoDebugExtension``, which is documented to run after any
masking extension - so the policy is inserted at index 0 rather than appended.
That is the exact inverse of the resource-policy extension's append, and for a
symmetric reason: the resource policy gates BEFORE execution, so it wants to
run first; the error policy rewrites AFTER it, so it wants to finish last.

Sync and async execution share one implementation. The teardown is a plain
synchronous generator - the engine enters sync generator hooks on the async
path too - so there is exactly one masking code path and no color-specific
branch to keep in parity.
"""

from __future__ import annotations

import copy
from collections.abc import Iterator
from typing import Any

from django.conf import settings
from graphql import GraphQLError
from graphql.execution import ExecutionResult as GraphQLExecutionResult
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.types.execution import ExecutionResult as StrawberryExecutionResult

from .. import logger
from ..error_policy import DEFAULT_ERROR_POLICY, ErrorPolicy, new_correlation_id

__all__ = ["DjangoErrorPolicyExtension", "mask_execution_result", "masking_is_active"]


def _is_unexpected(error: GraphQLError) -> bool:
    """Whether ``error`` reached the wire by accident (spec-048 Decision 8).

    Three cases, in the order graphql-core produces them:

    - ``original_error is None`` - a parse, syntax, or validation error, or an
      error graphql-core constructed itself with nothing behind it. Nothing
      raised it; its message describes the client's own request. Not masked.
    - ``original_error`` IS a ``GraphQLError`` - something raised a GraphQL error
      deliberately. Every framework rejection does this (the invalid-GlobalID
      boundary, the resource bounds, the connection / keyset / filter argument
      rejections, and the mutation pipeline's authorization denial), and a
      consumer raising ``GraphQLError`` is making the same statement about their
      own message. Not masked.
    - anything else - a plain Python exception that escaped a resolver or hook.
      Masked.

    **The rule reads through graphql-core's ``located_error`` wrapping, which is
    why it covers the completion phase as well as the resolve phase.** Every
    exception graphql-core surfaces from a field - whether it escaped the
    resolver, escaped an awaited value, or was raised while COMPLETING the
    resolved value (non-nullable ``null`` propagation, list-item completion, a
    custom scalar's ``serialize``) - arrives as a ``GraphQLError`` whose
    ``original_error`` IS that exception. So a resolver failure surfaced through
    value completion is still an unexpected plain exception here and is still
    masked; graphql-core's own completion ``TypeError`` is masked for the same
    structural reason, which is the fail-closed direction. Only a completion
    error whose ``original_error`` a consumer deliberately typed as a
    ``GraphQLError`` travels unchanged.

    The rule is structural rather than an allowlist of ``extensions.code``
    values on purpose: an allowlist must be extended by every future rejection
    site and fails OPEN when it is not, while this fails CLOSED for every new
    exception type the package or a consumer ever raises.
    """
    original = error.original_error
    if original is None:
        return False
    return not isinstance(original, GraphQLError)


def _masked(error: GraphQLError, policy: ErrorPolicy) -> GraphQLError:
    """Return the client-safe replacement for one unexpected ``error``.

    The location information - ``nodes``, ``source``, ``positions``, and ``path``
    - is deliberately RETAINED. It names which field of the client's own document
    failed, which the client already knows and which a client needs in order to
    report the failure usefully; nothing about it comes from the server's
    internals. What is dropped is the message and ``original_error``, which are
    the parts written by whatever raised.
    """
    correlation_id = new_correlation_id()
    logger.error(
        "Unhandled exception during GraphQL execution; the client received the "
        "policy message and correlation id %s.",
        correlation_id,
        exc_info=error.original_error,
    )
    return GraphQLError(
        message=policy.message,
        nodes=error.nodes,
        source=error.source,
        positions=error.positions,
        path=error.path,
        original_error=None,
        extensions={policy.correlation_extension_key: correlation_id},
    )


def _degraded(policy: ErrorPolicy) -> GraphQLError:
    """The floor: the policy message alone, with no location and no correlation id.

    Returned only when masking one error RAISED - a hostile ``original_error``
    property, an ``extensions`` map that misbehaves, an error object that is not
    the shape it claims. Nothing is read off the offending error to build this,
    because whatever was read is what failed; and no correlation id is minted,
    because there is no exception this one could be resolved to in the log. The
    server-side log record names the failure instead.
    """
    return GraphQLError(message=policy.message)


def masking_is_active(policy: ErrorPolicy) -> bool:
    """Whether ``policy`` masks anything for the operation being answered now.

    Both seams ask this one question, so neither can drift on the ``DEBUG``
    gate. ``settings.DEBUG`` is read per operation rather than captured at schema
    construction: a schema object outlives a settings override, and the answer
    that matters is the one true while the response is being built.
    """
    return policy.enabled and not settings.DEBUG


def schema_error_policy(schema: Any) -> ErrorPolicy:
    """The resolved policy carried by ``schema``, or the package default.

    A plain ``strawberry.Schema`` a consumer wired the extension into by hand has
    no ``error_policy`` attribute; that is a supported standalone use, so it falls
    back rather than raising. The ``isinstance`` gate is the same fail-closed
    reasoning applied to a WRONG attribute: something that is not an
    ``ErrorPolicy`` cannot be asked whether masking is enabled, and treating its
    truthiness as an answer would let an unrelated ``schema.error_policy``
    silently disable masking. Either way the fallback is the MASKING one -
    ``DEFAULT_ERROR_POLICY`` - because an extension whose whole job is to mask
    must not become a no-op because it could not find its configuration.
    ``DjangoSchema`` always supplies a valid one, validated at construction.
    """
    policy = getattr(schema, "error_policy", None)
    return policy if isinstance(policy, ErrorPolicy) else DEFAULT_ERROR_POLICY


def mask_execution_result(result: Any, policy: ErrorPolicy) -> Any:
    """Return the client-safe value for one completed or per-event ``result``.

    ``result`` itself is returned whenever nothing needed masking, so the common
    path allocates nothing and the caller can test identity to learn whether the
    policy did anything. Otherwise a SHALLOW COPY carries the rewritten error
    list: the object the engine assigned to ``execution_context.result`` keeps its
    originals, so an extension reading ``original_error`` after this ran still
    reads what was raised.

    Order and arity are preserved - every error keeps its position whether it was
    masked or not, so a client matching errors to its document by index is
    unaffected.

    **Masking FAILS CLOSED.** A masking failure is a disclosure risk, never a
    reason to fall back to the original text: one error that cannot be masked
    degrades to the policy message alone, and a result whose error list cannot
    even be read degrades to a single policy-message error with no ``data``. Both
    degrades are logged server-side with a traceback, so the failure is
    diagnosable without being publishable.
    """
    try:
        errors = result.errors
        if not errors:
            return result
        replacements = [_replacement_for(error, policy) for error in errors]
        if all(new is old for new, old in zip(replacements, errors, strict=True)):
            return result
        masked = copy.copy(result)
        masked.errors = replacements
        return masked
    except Exception:
        logger.exception(
            "The error policy could not read the execution result's errors; the response "
            "degrades to the policy message alone (fail closed).",
        )
        return StrawberryExecutionResult(data=None, errors=[_degraded(policy)])


def _replacement_for(error: Any, policy: ErrorPolicy) -> Any:
    """Classify and mask one error, degrading to the policy message if that raises."""
    try:
        if not _is_unexpected(error):
            return error
        return _masked(error, policy)
    except Exception:
        logger.exception(
            "The error policy could not classify or mask one execution error; the entry "
            "degrades to the policy message alone (fail closed).",
        )
        return _degraded(policy)


class DjangoErrorPolicyExtension(SchemaExtension):
    """Replace unexpected exception messages with a stable message plus a correlation id.

    Installed on every ``DjangoSchema`` unless the consumer supplied their own
    entry. The policy object is resolved once at schema construction and read
    from ``schema.error_policy``; this extension holds no configuration of its
    own, so a bare class entry and a factory entry behave identically.

    Active only when the policy is enabled AND the schema is not in debug
    execution. Under ``settings.DEBUG`` the extension is a pass-through: the
    unmasked message is the reason a developer set the setting, and a
    development schema has no untrusted reader to protect the message from.
    """

    def _policy(self) -> ErrorPolicy:
        """The schema's resolved policy, or the package default."""
        return schema_error_policy(self.execution_context.schema)

    def _process_result(self, result: Any, policy: ErrorPolicy) -> None:
        """Adopt the masked error list onto the result the transport will render.

        The masking itself belongs to ``mask_execution_result``, which the
        subscription seam shares; this method is only the assignment. Assigning
        ``errors`` cannot fail for either shape reaching it - both are mutable
        attribute holders and the caller's ``isinstance`` gate admits nothing
        else - so there is no third degrade here.
        """
        masked = mask_execution_result(result, policy)
        if masked is not result:
            result.errors = masked.errors

    def on_operation(self) -> Iterator[None]:
        """Apply the policy to the completed result, once, at teardown.

        The completed result is the WHOLE response for a query or a mutation, and
        for a subscription it is only the operation's end - each event was already
        masked at the transport's result source (see the module docstring). A
        ``result`` that is neither execution-result shape is a sync parse or
        validation early-return, which has nothing masked to begin with; the async
        path's ``PreExecutionError`` IS a strawberry ``ExecutionResult``, and its
        errors carry no ``original_error``, so it passes through the classifier
        untouched rather than being excluded by shape.
        """
        yield
        policy = self._policy()
        if not masking_is_active(policy):
            return
        result = self.execution_context.result
        if isinstance(result, (GraphQLExecutionResult, StrawberryExecutionResult)):
            self._process_result(result, policy)
