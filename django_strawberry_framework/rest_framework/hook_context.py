"""The frozen serializer-hook context + upload metadata (the hardening pass).

The consumer hooks (``get_serializer_kwargs`` / ``get_serializer_injected_data`` /
``get_serializer_save_kwargs``) no longer receive the LIVE located model instance:
a mutable target in consumer hands before the write is an attack surface (an
override could ``setattr`` unvalidated values that ``serializer.save()`` then
persists, or re-point ``pk`` at a row the caller was never authorized for). They
receive this frozen ``SerializerHookContext`` instead - the operation kind, the
pinned write alias, and the authorized target's pk snapshot - everything the
documented use cases (branching create-vs-update, routing an extra query into the
transaction, keying server data to the target row) actually need, with nothing
mutable. A hook that needs more of the row reads it itself through the pinned
alias (a visible, auditable query) rather than through a privileged live object.

``UploadMetadata`` is the frozen stand-in for an uploaded file in the DATA VIEW
the hooks receive: the authoritative upload objects (whose streams are
stateful - a hook that ``read()``s one would exhaust it before validation) stay
exclusively on the framework-built serializer ``data`` and reach only the
serializer's own validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SerializerHookContext:
    """The immutable context every serializer consumer hook receives.

    - ``operation`` - ``"create"`` or ``"update"`` (the mutation's declared kind).
    - ``write_alias`` - the pipeline's pinned write alias; a hook that queries
      routes through it so the read joins the one transaction.
    - ``instance_pk`` - the authorized target's pk SNAPSHOT (captured immediately
      after the locate, before any consumer code ran); ``None`` on create.
    """

    operation: str
    write_alias: str
    instance_pk: Any


@dataclass(frozen=True, slots=True)
class UploadMetadata:
    """The frozen upload descriptor standing in for a file value in hook data views.

    Carries what a hook can safely branch on (``name`` / ``size`` /
    ``content_type``); the stateful upload object itself never reaches a hook -
    it stays on the authoritative serializer ``data`` for validation to consume
    exactly once.
    """

    name: str | None
    size: int | None
    content_type: str | None
