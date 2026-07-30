"""The one place the package touches Django's private request-body internals.

``views.py``'s cumulative body cap (spec-046 Decision 7) needs an answer to
exactly one question - "is this request body larger than ``limit`` bytes?" - and
it must obtain that answer *without* first materializing the body it may be
about to refuse. :func:`body_exceeds_limit` is that answer, and this module is
the only file in the package that names ``HttpRequest._stream``,
``HttpRequest._body``, or ``HttpRequest._read_started``. Centralizing them here
rather than spreading them across the two view classes is what makes the
compatibility surface with Django's request object auditable from one file and
pinnable to one documented contract.

Why the public API cannot do this
---------------------------------

``HttpRequest.body`` is the public way to obtain a request body, and it is
structurally unusable for a *cap*: it performs an unbounded ``self.read()`` that
copies the whole request into one ``bytes`` value and only then returns it, so
``len(request.body) > limit`` detects an over-limit body strictly *after* the
attacker-sized allocation the limit exists to prevent. On ASGI that allocation
also re-reads a ``SpooledTemporaryFile`` which
``django.core.handlers.asgi.ASGIHandler.read_body`` may already have rolled to
disk past ``FILE_UPLOAD_MAX_MEMORY_SIZE`` - synchronously, on the event loop, for
the async view.

Django 6.0's own ``HttpRequest.body`` narrows that window: it seeks a *seekable*
stream to its end and checks the real buffered size against
``DATA_UPLOAD_MAX_MEMORY_SIZE`` before reading. The **Django 5.2.0 floor this
card supports has no such check** - only a ``CONTENT_LENGTH`` comparison - so an
absent declaration, an understated one, or ``DATA_UPLOAD_MAX_MEMORY_SIZE = None``
leaves that read unbounded there. The package cap therefore has to measure the
body itself on every supported release, and measuring it means reaching for the
stream Django keeps private.

The Django contract this module pins
------------------------------------

Read out of ``django/http/request.py`` (and the two handler modules) at both
supported versions - Django 5.2.0 and 6.0.5 - not from memory. The three
attributes behave identically across them; only ``body``'s own size checks
differ, which is the reason this module exists.

- ``_body`` is set as an *instance* attribute, once, by ``HttpRequest.body``
  after it has read the stream. Neither release declares a class-level default,
  so ``hasattr(request, "_body")`` is an exact test for "the body has already
  been materialized" - the same test ``HttpRequest.body`` and
  ``_load_post_and_files`` themselves perform.
- ``_read_started`` is initialized to ``False`` by ``WSGIRequest.__init__`` and
  ``ASGIRequest.__init__`` - **not** by ``HttpRequest.__init__``, so a bare
  ``HttpRequest`` has no such attribute - and set to ``True`` by
  ``HttpRequest.read`` / ``readline``. ``HttpRequest.body`` raises
  ``RawPostDataException`` when it is true and ``_body`` is absent.
- ``_stream`` is the byte source. ``ASGIRequest`` assigns the
  ``SpooledTemporaryFile`` that ``read_body`` filled; ``WSGIRequest`` assigns a
  ``LimitedStream`` that truncates reads at ``CONTENT_LENGTH``;
  ``django.test.AsyncRequestFactory`` also assigns a ``LimitedStream``. After
  materializing, ``HttpRequest.body`` closes the old stream and replaces it with
  ``BytesIO(self._body)``, so substituting a rewound ``BytesIO`` for a consumed
  stream is a shape Django both produces and accepts.

Note which attribute this module never writes: ``_body``. Filling Django's cache
would make ``HttpRequest.body`` short-circuit past its own
``DATA_UPLOAD_MAX_MEMORY_SIZE`` check, so the bounded branch hands its bytes back
as a *stream* instead and leaves the property fully in charge (see
:func:`_bounded_read_exceeds_limit`). The package's job is to add a ceiling, never
to remove Django's.

Seekability, measured rather than assumed
-----------------------------------------

- ``LimitedStream`` subclasses ``io.IOBase``, so it *declares* ``seekable()`` and
  returns ``False``, and its ``tell()`` raises ``io.UnsupportedOperation``. WSGI
  and the async test client therefore take the bounded-read branch.
- ``tempfile.SpooledTemporaryFile`` is seekable in fact on every supported
  Python, but only *declares* it from 3.11, where it became an ``io.IOBase``
  subclass. On the **Python 3.10 floor the attribute is absent entirely**
  (verified: ``hasattr(spool, "seekable")`` is ``False`` at 3.10.19 and ``True``
  at 3.14.2), while ``tell()`` / ``seek()`` work and return positions on both.
  That is why :func:`_declares_seekable` believes ``seekable()`` when the method
  exists and otherwise defers to ``tell()``: anything narrower would silently drop
  the ASGI spool onto the read branch at the exact floor the card protects.
- Neither production stream misbehaves, but neither is *constructed here*: the
  byte source is whatever the ASGI server, ``WSGIRequest``, or a consumer's
  middleware installed, so every capability call the probe makes is guarded and
  the probe reports **three** outcomes rather than two - measurable, safely
  unmeasurable with the position provably intact, or a position it could not
  prove it restored, which fails closed (see :class:`_Probe`).

What this module deliberately does not do
-----------------------------------------

It never raises ``HTTPException`` and never looks at settings: the cap's policy -
which limit applies, and what the ``413`` says - stays in
``views.py::_RequestBodyBoundaryMixin``. A stream failure is reported as a
``bool``, in the fail-closed direction, rather than as an exception of its own, so
this module cannot turn a hostile or unusual stream into an unrelated ``500``. It
also never touches a multipart request; ``views.py`` returns before calling here,
because reading a multipart body would defeat Django's streaming upload handlers
(spec-046 Decision 7 step 3).

The one thing it does emit is a single ``WARNING`` record on the
:attr:`_Probe.CORRUPTED` verdict (see :data:`_CORRUPTED_PROBE_LOG_MESSAGE`),
because that is the one refusal whose *reason* is deliberately invisible to the
client and therefore invisible to an operator too. It changes nothing on the wire.
"""

from __future__ import annotations

import os
from enum import Enum
from io import BytesIO
from typing import TYPE_CHECKING, Any

from . import logger

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from django.http import HttpRequest

__all__ = ("body_exceeds_limit",)


#: Ceiling on one bounded ``read()`` call. The bounded branch never reads more
#: than ``limit + 1`` bytes in total, so this only caps the size of a single
#: allocation on the way there: a mount configured with a very large limit must
#: not turn one hostile request into one very large ``read()``.
_READ_CHUNK_BYTES = 64 * 1024

#: The one server-side record of a :attr:`_Probe.CORRUPTED` verdict, and the only
#: signal this module emits. The caller's answer to the client is deliberately
#: indistinguishable from an ordinary over-limit refusal - Decision 9's
#: non-attributability applies to this branch as much as to the rest of the
#: boundary - which leaves an operator with a body-limit rejection for a request
#: that may not be oversized at all and no way to tell the two apart. So the
#: distinction is recorded where it belongs: server side, at ``WARNING``, the
#: level the package already uses for a condition a deployment should look at but
#: which is not this process's error (``types/finalizer.py``,
#: ``optimizer/nested_planner.py``). ``consumers.py``'s fail-closed revalidation
#: uses ``logger.exception`` instead because it runs inside an ``except`` block and
#: has a traceback worth carrying; a failed restore may simply have returned the
#: wrong position without raising, so there is no exception to attach.
_CORRUPTED_PROBE_LOG_MESSAGE = (
    "The GraphQL request-body size probe moved this request's stream (%s) and could not "
    "verify that it restored the original position, so the body is reported as over-limit "
    "(fail closed) rather than read from an unknown offset. The client sees the endpoint's "
    "ordinary body-limit rejection, which says nothing about this condition by design - so if "
    "a request that is NOT oversized was refused, the stream installed by the ASGI server or "
    "by a middleware is what does not report positions coherently, not the configured limit."
)


class _Probe(Enum):
    """The two non-numeric outcomes of a size probe, kept apart on purpose.

    The probe used to answer with an ``int`` or ``None``, and ``None`` had to
    carry two incompatible meanings: "measure it by reading instead" and "this
    stream is no longer in a state anything can safely read". Collapsing those
    into one sentinel is what let a failed position-restore fall through to a
    bounded read that then read from the wrong offset, so the two states are
    named (review Low 6).

    - :attr:`UNMEASURABLE` - the probe declined or failed, and the stream is
      **known** to be exactly where it started, so the bounded read is safe and
      is the answer.
    - :attr:`CORRUPTED` - the probe moved the stream and could not prove it put
      it back. There is no safe read left, so the caller fails closed: the
      request is refused as over-limit, because the package can no longer prove
      that it is not, and the bytes a read would return are no longer the
      request's bytes.
    """

    UNMEASURABLE = "unmeasurable"
    CORRUPTED = "corrupted"


def body_exceeds_limit(request: HttpRequest, limit: int) -> bool:
    """Whether ``request``'s body is longer than ``limit`` bytes.

    Answers in the cheapest way the request's actual state allows, in
    descending order of preference:

    1. **Already materialized** (``_body`` present, e.g. a urlencoded body some
       consumer middleware read on the way in). The allocation happened before
       the view ran and cannot be undone, so the length is simply measured - the
       caller must still refuse an over-limit body rather than process it. This
       rung used to be reached by Django's own ``CsrfViewMiddleware``, which
       reads ``request.POST`` for every cookie-bearing POST; it no longer is,
       because ``views.py`` re-enters CSRF from *inside* the view, after this
       measurement (spec-046 Decision 18). What remains reachable is a
       consumer's own inbound body read, which no application-level ordering can
       precede.
    2. **Measurable without reading** (a seekable stream, which is what ASGI's
       spooled body file is). The size is probed with ``seek`` / ``tell``, the
       original position is restored, and nothing is read or copied. This is the
       branch that makes an over-limit ASGI request cost no allocation at all.
    3. **Neither** (a genuinely non-seekable stream: WSGI's ``LimitedStream``,
       the async test client, a custom stream - or a seekable one whose probe
       came out at zero or less, which is a measurement failure rather than an
       empty body, see :func:`_measured_remaining`). The body is read in bounded
       chunks up to ``limit + 1`` bytes - one byte more than the largest legal
       body, which is the least information that can distinguish "at the limit"
       from "over it" - and no further. An allowed body is handed back as a
       rewound stream, so ``HttpRequest.body`` still runs normally over the
       original bytes and Django's own ceiling still applies.

    4. **Not safely readable at all** - the probe moved a stream it could not
       prove it put back (:attr:`_Probe.CORRUPTED`). The request is refused as
       over-limit: reading from an unknown offset would hand Strawberry bytes
       that are not the request's, and an application that cannot measure a body
       must not process it. This is the one branch that answers ``True`` without
       a measurement, and it is the fail-closed direction (review Low 6). It is
       also the one branch that logs: the client cannot be told this refusal is
       different from an ordinary over-limit one, so the operator is
       (:data:`_CORRUPTED_PROBE_LOG_MESSAGE`).

    Returns ``False`` without measuring anything in two states the package
    cannot bound and must not pretend to: no ``_stream`` at all (a synthetic
    ``HttpRequest``), and a stream some earlier component already read from
    without caching ``_body``. In the second state ``HttpRequest.body`` itself
    raises ``RawPostDataException``, so the request cannot be processed by
    anything downstream either; measuring is impossible and translating another
    component's error into a misleading ``413`` would be worse than deferring.
    """
    if hasattr(request, "_body"):
        return len(request._body) > limit
    stream = getattr(request, "_stream", None)
    if stream is None or getattr(request, "_read_started", False):
        return False
    remaining = _measured_remaining(stream)
    if remaining is _Probe.CORRUPTED:
        logger.warning(_CORRUPTED_PROBE_LOG_MESSAGE, type(stream).__name__)
        return True
    if remaining is _Probe.UNMEASURABLE:
        return _bounded_read_exceeds_limit(request, stream, limit)
    return remaining > limit


def _measured_remaining(stream: Any) -> int | _Probe:
    """The unread byte count of ``stream``, or which way the probe failed.

    Three outcomes, never two (review Low 6): a positive ``int``,
    :attr:`_Probe.UNMEASURABLE` ("ask the bounded read instead", with the stream
    provably untouched), or :attr:`_Probe.CORRUPTED` ("nothing may read this
    stream now"). "The body is empty" is not among them, which is enforced rather
    than merely intended - see below.

    Every call into ``stream`` is guarded, because ``stream`` is the one object in
    this file the package did not construct: it is whatever the ASGI server,
    ``WSGIRequest``, or a consumer's middleware installed, and a capability method
    that raises is a compatibility fact rather than a package bug. The guards
    catch ``Exception`` rather than an enumerated tuple on purpose - enumerating
    the types a foreign stream may raise is exactly the fragility this closes, and
    the failure of a *probe* is never a reason to abort a request with a ``500``.
    ``BaseException`` is deliberately not caught, so cancellation and
    ``KeyboardInterrupt`` still propagate.

    What each failure means for the position is what decides its outcome:

    - ``seekable()`` raising, or answering ``False``, and ``tell()`` raising all
      happen **before** anything moves, so they are ``UNMEASURABLE``. A stream
      that declares itself unseekable is also believed without being poked: a
      ``seek`` on it is undefined and a silently-misbehaving one would corrupt the
      read position for the request that follows. When ``seekable`` is absent
      entirely - the Python 3.10 ``SpooledTemporaryFile`` shape, i.e. the ASGI
      body file at the supported floor - capability is decided by ``tell()``
      instead, which the same ``io.UnsupportedOperation`` reports for a
      pipe-backed stream.
    - the seek to the end raising leaves the position **unknown**, so it is not
      trusted either way: the restore runs regardless, and the outcome is
      ``UNMEASURABLE`` only if the restore proves the original position is back.
    - the restore failing - raising, or landing somewhere other than where the
      stream started - is ``CORRUPTED``. It is verified with a second ``tell()``
      rather than inferred from "``seek`` did not raise", because "known to be
      intact" has to mean measured: a stream whose coordinates are incoherent
      (a ``tell()`` answering in the coordinates of the whole HTTP message rather
      than of the body it exposes) accepts the restore and still ends up
      somewhere else, and the bounded read would then read the wrong bytes -
      previously it silently produced an empty body.
    - the subtraction failing (a ``seek`` that returns ``None``, or anything else
      that is not a number - legal for a stream that simply does not report
      positions) is ``UNMEASURABLE``, because the restore already succeeded by
      then.

    Why a probed count of zero or less is a measurement FAILURE
    ----------------------------------------------------------

    ``0`` is the one numeric answer a size probe must never hand back, because
    :func:`body_exceeds_limit` reads it as "within the limit" and the request
    then goes straight to ``HttpRequest.body`` with **no package bound at
    all** - and at the Django 5.2.0 floor that property's only ceiling is the
    ``CONTENT_LENGTH`` this cap exists precisely not to trust. Answering it on
    the strength of two numbers is therefore fail-open, and the previous
    ``max(end - position, 0)`` did exactly that for both shapes of an
    incoherent pair: a ``tell()`` that over-reports (a wrapper answering in the
    coordinates of the whole message rather than of the body) and a
    ``seek(0, SEEK_END)`` that under-reports (a queue- or iterator-backed
    stream that can report a position but not take one, so it returns the
    offset it was handed). Both left every byte unread and every byte allowed.

    Verifying a zero costs exactly one ``read`` call, so the fail-safe
    direction is to verify it: anything at or below zero is ``UNMEASURABLE`` and
    the bounded read supplies the bound. A genuinely empty body is the cheapest
    request there is, and it still ends up allowed - by measurement rather than
    by assumption.

    What this cannot catch, stated rather than papered over: a *plausible* lie -
    an ``end`` that is wrong but still ahead of ``position`` - is
    indistinguishable from a measurement without reading the bytes it claims to
    describe, which is the very work the probe exists to avoid. An incoherent
    pair is the whole class of lie a probe can detect, and neither production
    stream tells any (``ASGIRequest``'s spool and ``WSGIRequest``'s
    ``LimitedStream`` both measure honestly on both supported interpreters); the
    shapes above are consumer middleware and custom ASGI servers, which is
    exactly where a silent fail-open would be least visible.

    The position is restored before the pair is judged - and before the failure
    of the end-seek is judged - so the bounded read that follows an
    ``UNMEASURABLE`` verdict always starts where the request started.
    """
    if not _declares_seekable(stream):
        return _Probe.UNMEASURABLE
    try:
        position = stream.tell()
    except Exception:  # a probe that cannot report a position has not moved one
        return _Probe.UNMEASURABLE
    try:
        end = stream.seek(0, os.SEEK_END)
    except Exception:  # the position is now unknown rather than known-intact
        end = None
        probed = False
    else:
        probed = True
    if not _position_restored(stream, position):
        return _Probe.CORRUPTED
    if not probed:
        return _Probe.UNMEASURABLE
    try:
        remaining = end - position
    except TypeError:
        return _Probe.UNMEASURABLE
    if remaining <= 0:
        return _Probe.UNMEASURABLE
    return remaining


def _declares_seekable(stream: Any) -> bool:
    """Whether ``stream`` may be size-probed at all, without moving it.

    ``True`` covers both shapes the probe supports: a stream whose ``seekable()``
    says yes, and one with no ``seekable`` method at all (the Python 3.10
    ``SpooledTemporaryFile`` - the ASGI body file at the supported floor - where
    capability is decided by ``tell()`` a moment later instead). A ``seekable()``
    that raises is treated exactly like one that answered ``False``: nothing has
    moved, so the bounded read is both available and correct.
    """
    seekable = getattr(stream, "seekable", None)
    if not callable(seekable):
        return True
    try:
        return bool(seekable())
    except Exception:  # a capability query that fails answers no, not maybe
        return False


def _position_restored(stream: Any, position: Any) -> bool:
    """Whether ``stream`` is provably back at ``position``.

    Verified with ``tell()`` rather than inferred from a ``seek`` that did not
    raise, because :func:`_measured_remaining`'s ``CORRUPTED`` verdict has to mean
    "not known to be intact", and a stream whose coordinates are incoherent
    accepts the restore while ending up somewhere else entirely.
    """
    try:
        stream.seek(position)
        return bool(stream.tell() == position)
    except Exception:  # an unverifiable restore is a failed restore
        return False


def _bounded_read_exceeds_limit(request: HttpRequest, stream: Any, limit: int) -> bool:
    """Read at most ``limit + 1`` bytes of ``stream``; report whether that exceeds ``limit``.

    Reads through ``request.read`` rather than ``stream.read`` so Django keeps
    ownership of its own bookkeeping: ``read`` sets ``_read_started`` and
    translates a stream ``OSError`` into ``UnreadablePostError``, which is what a
    consumer's error handling already expects on this path.

    Over the limit, the loop stops as soon as ``limit + 1`` bytes have arrived
    and the collected chunks are **never joined** - the remainder of the request
    is left unread and no over-limit ``bytes`` value is ever allocated.

    Under it, the prefix *is* the whole body (the loop only exits early on
    end-of-stream), and it is handed back by giving the request an equivalent
    byte source rather than by pre-filling Django's cache: the consumed stream is
    closed and replaced with a rewound ``BytesIO`` over those exact bytes, and
    ``_read_started`` is reset to the ``False`` the request was constructed with -
    which is now true again, because the installed stream is complete and
    unread. ``HttpRequest.body`` therefore still runs in full when Strawberry asks
    for the body: it returns the original bytes byte-for-byte, and, crucially, it
    still applies **Django's own** ``DATA_UPLOAD_MAX_MEMORY_SIZE`` ceiling in
    whatever form the installed Django implements it (a ``CONTENT_LENGTH``
    comparison at 5.2, plus a seekable-size check at 6.0 - which the substituted
    ``BytesIO`` now satisfies).

    Writing ``request._body`` directly instead was the obvious shape and is
    wrong: it makes ``HttpRequest.body`` short-circuit on its cache, silently
    disabling Django's ceiling for every request that took this branch, so a
    project relying on a ``DATA_UPLOAD_MAX_MEMORY_SIZE`` lower than the package cap
    would lose it. The package must add a ceiling, never remove one.
    """
    chunks = []
    read_so_far = 0
    while read_so_far <= limit:
        chunk = request.read(min(_READ_CHUNK_BYTES, limit + 1 - read_so_far))
        if not chunk:
            break
        chunks.append(chunk)
        read_so_far += len(chunk)
    if read_so_far > limit:
        return True
    stream.close()
    request._stream = BytesIO(b"".join(chunks))
    request._read_started = False
    return False
