"""The configured session engine's store resolver, shared across the opt-in boundary.

One function, and one reason for this module to exist: the ``SESSION_ENGINE``
expression that resolves a deployment's ``SessionStore`` class has two callers on
opposite sides of the package's opt-in boundary, and neither may drag the other
in.

* ``auth/sessions.py::uses_signed_cookie_sessions`` asks a *capability* question
  about the resolved class (can a WebSocket ``logout`` truthfully invalidate a
  session, or is there no server-side record to delete?).
* ``consumers.py::_refreshed_actor`` *instantiates* it to reload a WebSocket
  connection's session during the per-operation actor revalidation (spec-046
  Decision 11).

**Why it lives here and not in ``auth/sessions.py``.** The ``auth`` package is
structurally opt-in (spec-040 Decision 3): ``auth/__init__.py`` eagerly imports
``.mutations`` and ``.queries``, which pull the generated-mutation, declaration
registry, permission and Strawberry type machinery. Importing a submodule
executes its package's ``__init__`` first, so
``from .auth.sessions import session_store_class`` made the FIRST authenticated
WebSocket operation in a process that never opted into the GraphQL auth fields
import and register the entire auth subsystem on the event loop just to read one
settings string. Hosting the resolver in ``utils`` - which the transport layer and
the auth layer both already depend on - keeps one expression for the engine while
leaving ``auth`` opt-in, and keeps this module cycle-neutral: nothing here imports
``auth``, ``consumers``, ``routers``, or ``channels``, and both Django imports are
function-local, so importing this module costs nothing that is not already loaded.
"""

from __future__ import annotations


def session_store_class() -> type:
    """Resolve the configured ``SESSION_ENGINE``'s ``SessionStore`` class.

    The ONE expression that reads the deployment's session engine
    (``import_string(f"{settings.SESSION_ENGINE}.SessionStore")``) for both
    callers named in the module docstring. The resolution goes through Django's
    own ``import_string``, so a consumer-authored engine subclass resolves
    identically to a shipped one. ``settings`` is read at CALL time, never
    captured, so ``override_settings(SESSION_ENGINE=...)`` is honored.
    """
    from django.conf import settings
    from django.utils.module_loading import import_string

    return import_string(f"{settings.SESSION_ENGINE}.SessionStore")
