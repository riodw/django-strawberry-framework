"""``ErrorPolicy`` - what an unexpected exception says to a client in production.

Spec: ``docs/SPECS/spec-048-secure_output_defaults-0_0_14.md``.
Target release: ``0.0.14``.

graphql-core's default is to put an unhandled resolver or hook exception's
literal message into the response. That is the right default for a development
schema and the wrong one for a deployment: the message is written by whatever
raised it, which is frequently a library that had no idea it was addressing an
untrusted reader. A deployment does not become safe by remembering to install a
masking extension, so the package's required schema class installs a policy
instead.

The policy is deliberately narrow. It answers one question - *what does an
UNEXPECTED exception look like on the wire* - and nothing else:

- **The classification is structural, not a curated list.** A framework
  rejection is raised as a ``GraphQLError``; those are deliberate, audited,
  client-facing statements and travel unchanged. A parse or validation error has
  no originating exception at all and likewise travels unchanged. Everything
  else is an exception that reached the wire by accident, and only those are
  masked. A curated allowlist of error codes would have to be extended by every
  future rejection site and would fail OPEN the day someone forgot; this rule
  fails CLOSED for every new plain-Python exception.
- **The correlation identifier is the whole point.** Masking that only deletes
  information trades a disclosure for an unsupportable deployment. Each masked
  error carries a fresh ``uuid4().hex``, published to the client in the error's
  ``extensions`` and logged server-side alongside the original exception and its
  traceback, so an operator can resolve a user's complaint to one exception.
- **Development is untouched.** Under ``settings.DEBUG`` the policy is a
  pass-through; the local traceback is the reason the setting exists.

Resolved once at schema construction (``schema.py::DjangoSchema``) through
``resolve_error_policy``, exactly as the resource policy is: an invalid
deployment fails at startup rather than on a request, and no resolver re-reads
a setting.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

from .conf import error_policy_setting
from .exceptions import ConfigurationError, describe_value

__all__ = (
    "DEFAULT_ERROR_POLICY",
    "ErrorPolicy",
    "new_correlation_id",
    "resolve_error_policy",
)


@dataclass(frozen=True)
class ErrorPolicy:
    """The immutable production error policy for one schema.

    ``enabled``
        Whether unexpected exceptions are masked at all. ``True`` by default -
        the whole point of the policy is that safety is not opt-in. A consumer
        who owns their own masking sets it ``False`` explicitly, which is a
        recorded decision rather than an omission.

    ``message``
        The single stable string every masked error carries. It interpolates
        nothing from the original exception by construction: a message that
        embeds any part of what it is masking is not a mask.

    ``correlation_extension_key``
        The key the correlation identifier is published under in the GraphQL
        error's ``extensions`` map. Configurable because a deployment with an
        existing error contract may already have a name for this field.

    Frozen, so a resolver cannot widen its own request's policy.
    """

    enabled: bool = True
    message: str = "An unexpected error occurred."
    correlation_extension_key: str = "correlationId"

    def __post_init__(self) -> None:
        """Reject a malformed policy at construction, naming the offending field."""
        if not isinstance(self.enabled, bool):
            raise ConfigurationError(
                f"ErrorPolicy.enabled must be a bool; got {describe_value(self.enabled)}.",
            )
        for name in ("message", "correlation_extension_key"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ConfigurationError(
                    f"ErrorPolicy.{name} must be a non-empty string; got {describe_value(value)}.",
                )


#: The package default: masking on, a stable neutral message, the ``correlationId``
#: extensions key. Read whenever neither the schema argument nor the setting
#: supplies an override - so the fail-closed answer is the one a deployment gets
#: by doing nothing.
DEFAULT_ERROR_POLICY = ErrorPolicy()


def resolve_error_policy(explicit: ErrorPolicy | Mapping[str, Any] | None) -> ErrorPolicy:
    """Normalize the deployment's error policy once, at schema construction.

    Precedence, highest first: the ``DjangoSchema(error_policy=...)`` argument,
    the ``DJANGO_STRAWBERRY_FRAMEWORK["ERROR_POLICY"]`` mapping, and the package
    defaults. An ``ErrorPolicy`` instance passed explicitly is used as-is (it has
    already validated itself); a mapping from either source is applied over the
    package defaults so a deployment overrides only what it cares about.

    The structural twin of ``resource_policy.py::resolve_resource_policy`` - the
    two are deliberately the same shape, because a consumer who has learned how
    one schema-construction policy is configured has learned both.
    """
    if isinstance(explicit, ErrorPolicy):
        return explicit
    overrides = explicit if explicit is not None else error_policy_setting()
    if overrides is None:
        return DEFAULT_ERROR_POLICY
    if not isinstance(overrides, Mapping):
        raise ConfigurationError(
            "The error policy must be an ErrorPolicy or a mapping of option names "
            f"to values; got {describe_value(overrides)}.",
        )
    known = {field.name for field in fields(ErrorPolicy)}
    unknown = sorted(str(name) for name in overrides if name not in known)
    if unknown:
        raise ConfigurationError(
            f"Unknown error-policy option(s): {', '.join(unknown)}. "
            f"Valid options: {', '.join(sorted(known))}.",
        )
    return ErrorPolicy(**dict(overrides))


def new_correlation_id() -> str:
    """Return one fresh correlation identifier: 32 lowercase hexadecimal characters.

    ``uuid4().hex`` rather than a counter, a timestamp, or a request id: it is
    unique across processes and restarts without coordination, it carries no
    information about the deployment, and its format is fixed-width so a log
    grep for it cannot match anything else.

    One id is minted PER MASKED ERROR, not per operation. A response reporting
    two unrelated failures logs two exceptions, and a single shared id would
    make the log ambiguous exactly when an operator most needs it not to be.
    """
    return uuid.uuid4().hex
