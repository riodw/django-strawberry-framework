"""``DjangoErrorPolicyExtension`` - the response-side enforcement of ``ErrorPolicy``.

Spec: ``docs/SPECS/spec-048-secure_output_defaults-0_0_14.md``.
Target release: ``0.0.14``.

``error_policy.py`` owns the policy object; this module is the one place that
applies it. ``DjangoSchema`` installs the extension automatically, so a schema
built through this package does not leak an unexpected exception's message by
default.

One pass over a completed result: every error on it is classified and, when it is
unexpected, replaced by a fresh ``GraphQLError`` carrying the policy's stable
message and a correlation identifier, while the original exception is logged
server-side under that same identifier.

**There are two seams, because a response is not always one result.** A query or
mutation answered through ``schema.execute`` produces exactly one already-torn-down
result, so this extension's ``on_operation`` teardown is the whole story for it. A
STREAMED operation is not: a subscription delivers one ``ExecutionResult`` PER EVENT
through the result source the transport iterates, and a query or mutation run over a
streaming transport has its single result yielded from inside the operation
lifecycle - either way that teardown runs only when the operation ENDS, so the
errors would already be on the wire by the time it ran. The per-result seam is
therefore the transport's own result source
(``consumers.py::_stop_aware_results``), which masks each yielded value through
``mask_execution_result`` below, under the shared ``is_maskable_result`` shape gate.
One masking implementation, two places it is applied, and neither re-states the
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

__all__ = [
    "DjangoErrorPolicyExtension",
    "is_maskable_result",
    "mask_execution_result",
    "masking_is_active",
]


def _is_unexpected(error: Any) -> bool:
    """Whether ``error`` reached the wire by accident (spec-048 Decision 8).

    Three cases, in the order graphql-core produces them:

    - non-``GraphQLError`` - any arbitrary error object or plain Python exception
      present in ``errors``. Masked.
    - ``original_error is None`` on a ``GraphQLError`` - a parse, syntax, or
      validation error, or an error graphql-core constructed itself with
      nothing behind it. Nothing raised it; its message describes the client's
      own request. Not masked.
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

    The ``original_error`` read is a DIRECT attribute access rather than a
    defaulted ``getattr`` on purpose: a defaulted ``getattr`` cannot tell an
    attribute that is ABSENT from one whose read RAISES, and "absent" is the
    deliberate-delivery answer. An error object that will not let the rule read
    behind it (a ``GraphQLError`` subclass whose ``original_error`` property
    raises, reachable only from a consumer extension that put its own object in
    the result's error list) is exactly an error the policy cannot vouch for, so
    the read's failure is contained by the caller's per-entry degrade - the
    fail-closed direction - instead of being answered as if it said "deliberate".

    The rule is structural rather than an allowlist of ``extensions.code``
    values on purpose: an allowlist must be extended by every future rejection
    site and fails OPEN when it is not, while this fails CLOSED for every new
    exception type the package or a consumer ever raises.
    """
    if not isinstance(error, GraphQLError):
        return True
    original = error.original_error
    if original is None:
        return False
    return not isinstance(original, GraphQLError)


def _masked(error: Any, policy: ErrorPolicy) -> GraphQLError:
    """Return the client-safe replacement for one unexpected ``error``.

    The location information - ``nodes``, ``source``, ``positions``, and ``path``
    - is deliberately RETAINED. It names which field of the client's own document
    failed, which the client already knows and which a client needs in order to
    report the failure usefully; nothing about it comes from the server's
    internals. What is dropped is the message and ``original_error``, which are
    the parts written by whatever raised.
    """
    correlation_id = new_correlation_id()
    original_error = getattr(error, "original_error", None) or (
        error if isinstance(error, Exception) else None
    )
    logger.error(
        "Unhandled exception during GraphQL execution; the client received the "
        "policy message and correlation id %s.",
        correlation_id,
        exc_info=original_error,
    )
    return GraphQLError(
        message=policy.message,
        nodes=getattr(error, "nodes", None),
        source=getattr(error, "source", None),
        positions=getattr(error, "positions", None),
        path=getattr(error, "path", None),
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

    The policy's ``message`` is the one thing still worth reading - it is what
    this floor exists to publish - but the read is guarded, because the floor
    itself is what every other failure lands on and a floor that can raise is
    not a floor. A defaulted ``getattr`` would not be enough: it suppresses only
    ``AttributeError``, and a policy that is an ``ErrorPolicy`` subclass whose
    ``message`` is a raising property passes the ``isinstance`` gate in
    ``schema_error_policy`` while raising anything else (``schema_error_policy``
    can catch a hostile read on the SCHEMA, but a hostile read on an admitted
    policy object is this function's to survive). A non-string or empty message
    is likewise refused: the floor's whole output is one publishable string, so
    anything else is replaced by the package default's message, which validated
    itself at construction.
    """
    try:
        message: Any = policy.message
    except Exception:
        message = None
    if not isinstance(message, str) or not message:
        message = DEFAULT_ERROR_POLICY.message
    return GraphQLError(message=message)


def masking_is_active(policy: ErrorPolicy) -> bool:
    """Whether ``policy`` masks anything for the operation being answered now.

    Both reads fail toward MASKING, because this is the question the mask asks:
    a policy whose ``enabled`` read raises - an ``ErrorPolicy`` subclass can
    smuggle a raising property past the ``isinstance`` gate in
    ``schema_error_policy`` - is treated as enabled, and a ``DEBUG`` that cannot
    be read at all is treated as not exactly ``True``. An unreadable ``DEBUG`` is
    not hypothetical: deleting the attribute (the proxy caches reads in its own
    ``__dict__``, so both layers must lose it) or answering a schema outside a
    configured Django process both raise on the read, and letting that escape
    would answer a masking question by exception - the query teardown would catch
    it into a whole-result floor and destroy healthy data beside the errors it
    should have masked, and the subscription seam would surface it mid-stream.
    A gate that cannot read its inputs therefore keeps the mask ON, which is the
    only direction that cannot leak.
    """
    try:
        enabled = policy.enabled
    except Exception:
        return True
    try:
        debug = settings.DEBUG
    except Exception:
        debug = None
    return enabled and debug is not True


def is_maskable_result(value: Any) -> bool:
    """Whether ``value`` is the execution-result shape this policy can rewrite.

    Both seams ask this one question, so neither can drift on the shape gate. The
    two admitted shapes are the only ones carrying a flat ``errors`` list this
    policy knows how to classify and replace; a strawberry ``PreExecutionError`` is
    itself an ``ExecutionResult`` and is admitted, contributing nothing to mask
    because its errors carry no ``original_error``.

    What the gate excludes is what makes it necessary rather than decorative. The
    operation-teardown seam meets a sync parse or validation early-return, which
    has nothing masked to begin with. The per-event seam meets a raw graphql-core
    incremental-delivery frame (``@defer`` / ``@stream``), whose errors are nested
    inside incremental payloads: masking it would take the fail-closed degrade -
    the policy cannot read its errors - and the degrade is an ``ExecutionResult``,
    the shape the transport tests for to decide the frame is unrenderable and the
    operation must be rejected. Excluding it by shape leaves that rejection intact,
    which discloses nothing: the frame never reaches the wire at all.
    """
    return isinstance(value, (GraphQLExecutionResult, StrawberryExecutionResult))


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
    try:
        policy = getattr(schema, "error_policy", None)
    except Exception:
        return DEFAULT_ERROR_POLICY
    return policy if isinstance(policy, ErrorPolicy) else DEFAULT_ERROR_POLICY


def mask_execution_result(result: Any, policy: ErrorPolicy) -> Any:
    """Return the client-safe value for one completed or per-event ``result``.

    ``result`` itself is returned whenever nothing needed masking, so the common
    path allocates nothing and the caller can test identity to learn whether the
    policy did anything. Otherwise a SHALLOW COPY carries the rewritten error
    list: the object the engine assigned to ``execution_context.result`` keeps its
    originals, so an extension reading ``original_error`` after this ran still
    reads what was raised.

    The error list is MATERIALIZED before the emptiness check: a container that
    answers falsy while carrying entries (a lying ``__len__`` or ``__bool__``)
    would otherwise be waved through unclassified - the truthiness test trusts
    the container, iteration is what can be verified. The generator / iterator
    error list a stock result never carries is consumed by the same
    materialization, which is also what keeps ``zip``'s arity comparison honest.

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
        if errors is None:
            return result
        errors_list = list(errors)
        if not errors_list:
            return result
        replacements = [_replacement_for(error, policy) for error in errors_list]
        if all(new is old for new, old in zip(replacements, errors_list, strict=True)):
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
        schema = getattr(getattr(self, "execution_context", None), "schema", None)
        return schema_error_policy(schema)

    def _process_result(self, result: Any, policy: ErrorPolicy) -> None:
        """Adopt the masked result onto the value the transport will render.

        The masking itself belongs to ``mask_execution_result``, which the
        subscription seam shares; this method is only the assignment. Assigning
        the three result fields cannot fail for either stock shape reaching it -
        both are mutable attribute holders and the caller's ``isinstance`` gate
        admits nothing else. The complete assignment matters for the outer
        fail-closed degrade: when an error list cannot be read, the replacement
        deliberately drops ``data`` and ``extensions`` as well as the errors.
        If a consumer-supplied result subclass makes one of those assignments
        fail, replace the execution-context result itself with the safe stock
        shape rather than leaving the original data on the wire.
        """
        masked = mask_execution_result(result, policy)
        if masked is not result:
            try:
                result.data = masked.data
                result.errors = masked.errors
                result.extensions = masked.extensions
            except Exception:
                logger.exception(
                    "The error policy could not adopt the safe execution result; the "
                    "response is replaced with the policy message alone (fail closed).",
                )
                self.execution_context.result = StrawberryExecutionResult(
                    data=None,
                    errors=[_degraded(policy)],
                )

    def on_operation(self) -> Iterator[None]:
        """Apply the policy to the completed result, once, at teardown.

        The completed result is the WHOLE response for a query or a mutation
        upstream ran through ``schema.execute``, and for anything the transport
        streamed - every subscription, and a query or mutation over a streaming
        transport - it is only the operation's end, because each yielded result was
        already masked at the transport's result source (see the module docstring).
        The shape gate is ``is_maskable_result``, which carries what it admits and
        what it excludes.
        """
        yield
        try:
            policy = self._policy()
            if not masking_is_active(policy):
                return
            result = getattr(getattr(self, "execution_context", None), "result", None)
            if is_maskable_result(result):
                self._process_result(result, policy)
        except Exception:
            logger.exception(
                "The error policy encountered an unhandled exception during teardown; "
                "the response degrades to the policy message alone (fail closed).",
            )
            try:
                policy = self._policy()
            except Exception:
                policy = DEFAULT_ERROR_POLICY
            try:
                if hasattr(self, "execution_context") and self.execution_context is not None:
                    self.execution_context.result = StrawberryExecutionResult(
                        data=None,
                        errors=[_degraded(policy)],
                    )
            except Exception:
                pass
