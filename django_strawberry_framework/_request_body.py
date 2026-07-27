"""The one place the package touches Django's private request-body internals.

``views.py``'s cumulative body cap (spec-065 Decision 7) needs an answer to
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
  That is why :func:`_measured_remaining` trusts ``seekable()`` when the method
  exists and otherwise asks ``tell()``: anything narrower would silently drop the
  ASGI spool onto the read branch at the exact floor the card protects.

What this module deliberately does not do
-----------------------------------------

It never raises ``HTTPException`` and never looks at settings: the cap's policy -
which limit applies, and what the ``413`` says - stays in
``views.py::_RequestBodyBoundaryMixin``. It also never touches a multipart
request; ``views.py`` returns before calling here, because reading a multipart
body would defeat Django's streaming upload handlers (spec-065 Decision 7
step 3).
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.http import HttpRequest

__all__ = ("body_exceeds_limit",)


#: Ceiling on one bounded ``read()`` call. The bounded branch never reads more
#: than ``limit + 1`` bytes in total, so this only caps the size of a single
#: allocation on the way there: a mount configured with a very large limit must
#: not turn one hostile request into one very large ``read()``.
_READ_CHUNK_BYTES = 64 * 1024


def body_exceeds_limit(request: HttpRequest, limit: int) -> bool:
    """Whether ``request``'s body is longer than ``limit`` bytes.

    Answers in the cheapest way the request's actual state allows, in
    descending order of preference:

    1. **Already materialized** (``_body`` present, e.g. a urlencoded body
       ``CsrfViewMiddleware`` read to find its token). The allocation happened
       before the view ran and cannot be undone, so the length is simply
       measured - the caller must still refuse an over-limit body rather than
       process it.
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
    if remaining is not None:
        return remaining > limit
    return _bounded_read_exceeds_limit(request, stream, limit)


def _measured_remaining(stream: Any) -> int | None:
    """The unread byte count of ``stream``, or ``None`` when it cannot be measured.

    ``None`` means "ask the bounded read instead", never "the body is empty" -
    and that is enforced rather than merely intended, which is why the function
    ends in a comparison instead of a clamp.

    A stream that declares itself unseekable is believed without being poked: a
    ``seek`` on a stream whose own ``seekable()`` says no is undefined, and a
    silently-misbehaving one would corrupt the read position for the request
    that follows. When the method is absent - the Python 3.10
    ``SpooledTemporaryFile`` shape, i.e. the ASGI body file at the supported
    floor - capability is decided by ``tell()`` instead, which the same
    ``io.UnsupportedOperation`` (an ``OSError`` *and* a ``ValueError``) reports
    for a pipe-backed stream. Once ``tell()`` has answered, ``seek`` is trusted
    unguarded, exactly as Django 6.0's own ``HttpRequest.body`` trusts it.

    Why a probed count of zero or less is a measurement FAILURE
    ----------------------------------------------------------

    ``0`` is the one answer a size probe must never hand back, because
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
    direction is to verify it: anything at or below zero returns ``None`` and
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

    The position is restored unconditionally, before the pair is judged, so the
    bounded read that follows a refused measurement starts where the request
    started.
    """
    seekable = getattr(stream, "seekable", None)
    if callable(seekable) and not seekable():
        return None
    try:
        position = stream.tell()
    except (AttributeError, OSError, ValueError):
        return None
    end = stream.seek(0, os.SEEK_END)
    stream.seek(position)
    remaining = end - position
    if remaining <= 0:
        return None
    return remaining


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
