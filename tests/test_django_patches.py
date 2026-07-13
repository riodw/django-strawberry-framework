"""Django patch tests for DB connection wrapping and multi-database safety.

System-under-test: :mod:`django_strawberry_framework._django_patches`,
applied at app-load time by
:meth:`django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig.ready`.

The currently-shipped patch hardens
``SimpleTestCase._remove_databases_failures`` against Django Trac
#37064 (closed upstream as ``wontfix``):
<https://code.djangoproject.com/ticket/37064>. Without the patch, any
code path that replaces a connection method between ``setUpClass`` and
``tearDownClass`` crashes the cleanup loop with
``AttributeError: 'function' object has no attribute 'wrapped'``.
Django defines the classmethod on ``SimpleTestCase`` itself, so a
single patch on the base class covers ``TransactionTestCase`` and
``TestCase`` via normal inheritance - including direct
``SimpleTestCase`` subclasses, which ``TransactionTestCase`` is NOT in
the MRO of.

These tests do not require ``FAKESHOP_SHARDED=1``; they drive the
patched method directly against synthetic ``SimpleTestCase`` /
``TransactionTestCase`` subclasses with hand-built ``databases``
allow-lists. The test ``default`` alias is always present, so a
one-alias multi-DB scenario is enough to exercise both branches of
the patched loop. (The end-to-end demo shape from
<https://github.com/riodw/django-remove_databases_failures-demo> runs
under vanilla ``manage.py test`` rather than pytest-django and cannot
be reproduced 1:1 under our test runner - pytest-django's per-test
flush calls ``connection.cursor()`` mid-lifecycle and crashes on the
swapped cursor before reaching ``tearDownClass``. The unit tests
below isolate the bug class from that machinery.)
"""

from unittest import mock

import pytest
from django.db import connections
from django.test.testcases import SimpleTestCase, TestCase, TransactionTestCase

from django_strawberry_framework import _django_patches


def _database_failure(wrapped):
    if _django_patches._DatabaseFailure is None:
        pytest.skip("Django private _DatabaseFailure symbol is unavailable.")
    return _django_patches._DatabaseFailure(wrapped, "test message")


def test_apply_is_idempotent():
    """Repeated calls to :func:`apply` leave the patch installed.

    Pins the "ensure current state" contract called out in the module
    docstring. AppConfig.ready() may run more than once under some
    Django test runners; the patch must tolerate that.
    """
    _django_patches.apply()
    _django_patches.apply()  # second call should be a self-healing no-op
    assert _django_patches._patch_is_installed() is True


def test_apply_reinstalls_when_class_attribute_reverted():
    """``apply()`` re-installs the patch if a third party reverted the
    class attribute between calls.

    Pins the strengthened "re-entrant calls are no-ops; the patch
    re-installs if not currently present" contract on ``apply()``.
    Without this, a misbehaving test that swapped
    ``SimpleTestCase._remove_databases_failures`` without restoring
    would leave the class permanently in the unpatched state for the
    rest of the process - and the next ``apply()`` call would silently
    decline to re-install.
    """
    _django_patches.apply()
    assert _django_patches._patch_is_installed() is True

    # Capture the classmethod descriptor via ``__dict__`` (assigning a
    # bound method back via the attribute would replace the descriptor
    # with a regular function and break later tests).
    saved = SimpleTestCase.__dict__["_remove_databases_failures"]
    try:

        def _foreign(cls):
            pass

        SimpleTestCase._remove_databases_failures = classmethod(_foreign)
        assert _django_patches._patch_is_installed() is False

        _django_patches.apply()
        assert _django_patches._patch_is_installed() is True
    finally:
        SimpleTestCase._remove_databases_failures = saved


def test_patch_is_installed_on_simple_test_case():
    """``SimpleTestCase._remove_databases_failures`` is the patched
    version after :func:`apply` runs.

    Django defines the method on ``SimpleTestCase`` (not on
    ``TransactionTestCase``), so the patch is installed there. By the
    time pytest starts collecting, the patched version should already
    be in place via ``AppConfig.ready()``.
    """
    assert (
        SimpleTestCase._remove_databases_failures.__func__
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_inherited_by_transaction_test_case():
    """``TransactionTestCase`` inherits ``_remove_databases_failures``
    from ``SimpleTestCase`` - patching the base class covers the
    subclass for free.
    """
    assert (
        TransactionTestCase._remove_databases_failures.__func__
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_inherited_by_test_case():
    """``TestCase`` inherits ``_remove_databases_failures`` from
    ``SimpleTestCase`` (via ``TransactionTestCase``) - one patch
    covers the whole Django test-case hierarchy.
    """
    assert (
        TestCase._remove_databases_failures.__func__
        is _django_patches._patched_remove_databases_failures
    )


def test_patch_is_installed_returns_false_when_attribute_absent_from_class_dict():
    """Pin the ``installed is None`` branch of ``_patch_is_installed()``.

    Defensive contract: if a future Django release moves
    ``_remove_databases_failures`` off ``SimpleTestCase`` (e.g., onto a
    parent class, or removes it entirely),
    ``SimpleTestCase.__dict__.get(...)`` returns ``None`` rather than a
    classmethod descriptor. ``_patch_is_installed()`` must return
    ``False`` in that case so the next ``apply()`` call falls through
    to the install path rather than mis-reporting that the patch is
    already in place.
    """
    saved = SimpleTestCase.__dict__["_remove_databases_failures"]
    try:
        del SimpleTestCase._remove_databases_failures
        assert "_remove_databases_failures" not in SimpleTestCase.__dict__
        assert _django_patches._patch_is_installed() is False
    finally:
        SimpleTestCase._remove_databases_failures = saved


def test_patched_remove_databases_failures_unwraps_a_real_wrapper():
    """Happy path: when ``connection.<method>`` is a genuine
    ``_DatabaseFailure`` instance, the patched method unwraps it
    exactly as Django's upstream version does.

    Builds a ``TransactionTestCase`` subclass whose ``databases``
    allow-list excludes ``default``, wraps
    ``connections["default"].cursor`` with a ``_DatabaseFailure``
    pointing at an original (sentinel) callable, and invokes the
    patched method. The cursor must be restored to the sentinel.
    """

    class _NarrowTest(TransactionTestCase):
        databases = frozenset()  # exclude every alias including default

    connection = connections["default"]
    original_cursor = connection.cursor
    sentinel = mock.sentinel.original_cursor

    wrapper = _database_failure(sentinel)
    connection.cursor = wrapper
    try:
        _NarrowTest._remove_databases_failures()
        # Wrapper unwrapped -> method now equals the sentinel.
        assert connection.cursor is sentinel
    finally:
        connection.cursor = original_cursor


def test_patched_remove_databases_failures_skips_non_wrapper_methods():
    """The Trac #37064 fix proper: when ``connection.<method>`` is NOT
    a ``_DatabaseFailure`` instance (something replaced it without
    restoring the wrapper), the patched method leaves it alone instead
    of crashing on ``method.wrapped``.

    This is the load-bearing assertion of the whole patch - without
    the ``isinstance`` guard, the same setup raises
    ``AttributeError: 'function' object has no attribute 'wrapped'``.
    The companion test
    :func:`test_unpatched_remove_databases_failures_crashes_on_non_wrapper`
    pins that the crash IS real at our Django pin.
    """

    class _NarrowTest(TransactionTestCase):
        databases = frozenset()  # exclude every alias including default

    connection = connections["default"]
    original_cursor = connection.cursor

    def _plain_cursor(*args, **kwargs):
        return None  # explicitly not a ``_DatabaseFailure`` wrapper

    connection.cursor = _plain_cursor
    try:
        # Should NOT raise.
        _NarrowTest._remove_databases_failures()
        # And the replacement is left untouched (the patch declines to
        # restore a wrapper it never installed).
        assert connection.cursor is _plain_cursor
    finally:
        connection.cursor = original_cursor


def test_patched_remove_databases_failures_covers_direct_simple_test_case_subclass():
    """Direct ``SimpleTestCase`` subclasses - ``TransactionTestCase``
    is NOT in their MRO - must also get the unwrap-time protection.

    Pins that the patch is installed on ``SimpleTestCase`` itself, not
    only on ``TransactionTestCase``. Without this coverage, the patch
    silently bypasses the simplest kind of Django test class.
    """

    class _NarrowSimpleTest(SimpleTestCase):
        databases = frozenset()  # exclude every alias including default

    # MRO sanity-check the test's premise: ``TransactionTestCase`` is
    # NOT in the inheritance chain.
    assert TransactionTestCase not in _NarrowSimpleTest.__mro__

    connection = connections["default"]
    original_cursor = connection.cursor

    def _plain_cursor(*args, **kwargs):
        return None

    connection.cursor = _plain_cursor
    try:
        # Should NOT raise even though this class only inherits from
        # ``SimpleTestCase``. If the patch were still installed on
        # ``TransactionTestCase``, this call would raise.
        _NarrowSimpleTest._remove_databases_failures()
        assert connection.cursor is _plain_cursor
    finally:
        connection.cursor = original_cursor


def test_unpatched_remove_databases_failures_crashes_on_non_wrapper():
    """Pins that Trac #37064's bug shape IS still in Django at our pin.

    Temporarily reverts ``SimpleTestCase._remove_databases_failures`` to
    the genuine upstream classmethod the module captured at import time
    (``_original_remove_databases_failures``), exercises the same setup
    as the happy-path test above, and asserts that the crash happens
    inside the *installed* Django's own body. A Django upgrade that
    fixed the bug upstream makes this test fail (no ``AttributeError``
    raised), signalling that the package's patch can be retired. A
    hardcoded copy of the upstream body could not deliver that signal:
    the copy would keep crashing no matter what the installed Django
    ships.
    """
    # Capture the classmethod descriptor via ``__dict__`` so the
    # ``finally`` restore puts the patch back in its native shape (a
    # ``classmethod`` descriptor on ``SimpleTestCase``).
    patched = SimpleTestCase.__dict__["_remove_databases_failures"]
    captured = _django_patches._original_remove_databases_failures
    # Premise check: the import-time capture is genuinely upstream's
    # method, not this package's patch (the module is imported - and the
    # capture taken - before ``apply()`` ever runs).
    assert captured.__func__.__module__ == "django.test.testcases"

    SimpleTestCase._remove_databases_failures = captured
    try:

        class _NarrowTest(TransactionTestCase):
            databases = frozenset()  # exclude every alias including default

        connection = connections["default"]
        original_cursor = connection.cursor

        def _plain_cursor(*args, **kwargs):
            return None

        connection.cursor = _plain_cursor
        try:
            with pytest.raises(AttributeError, match="wrapped"):
                _NarrowTest._remove_databases_failures()
        finally:
            connection.cursor = original_cursor
    finally:
        SimpleTestCase._remove_databases_failures = patched


def test_apply_fails_loudly_when_database_failure_symbol_missing():
    """A private-Django shape change cannot silently disable the teardown patch."""
    with mock.patch.object(_django_patches, "_DatabaseFailure", None):
        with pytest.raises(RuntimeError, match="_DatabaseFailure"):
            _django_patches.apply()


def test_apply_fails_loudly_when_upstream_method_signature_changes():
    """The patch pins the classmethod arity its replacement assumes."""

    def changed(cls, extra):
        pass

    with mock.patch.object(
        _django_patches,
        "_original_remove_databases_failures",
        classmethod(changed),
    ):
        with pytest.raises(RuntimeError, match=r"expected \(cls\) signature"):
            _django_patches.apply()


def test_apply_fails_loudly_when_upstream_body_drifts():
    """A shape-passing but body-drifted Django must not get its teardown clobbered.

    The patch *reimplements* upstream's whole body rather than wrapping
    and delegating to it, so validation pins the captured original's
    source, not just the ``(cls)`` call shape. A future Django that
    keeps the classmethod signature but changes the body (renames
    ``_disallowed_connection_methods``, alters the ``_DatabaseFailure``
    protocol, or fixes Trac #37064 outright) would otherwise pass
    validation and have its working teardown replaced by a stale
    reimplementation that crashes with the very ``AttributeError`` class
    the patch exists to prevent. ``apply()`` must raise the targeted
    ``RuntimeError`` before installing anything.
    """
    saved = SimpleTestCase.__dict__["_remove_databases_failures"]
    try:

        def _foreign(cls):
            pass

        SimpleTestCase._remove_databases_failures = classmethod(_foreign)
        assert _django_patches._patch_is_installed() is False

        def _drifted(cls):
            """A (cls)-shaped upstream whose body renamed the method list."""
            for alias in connections:
                if alias in cls.databases:
                    continue
                connection = connections[alias]
                for name, _ in cls._forbidden_connection_methods:
                    method = getattr(connection, name)
                    setattr(connection, name, method.wrapped)

        with mock.patch.object(
            _django_patches,
            "_original_remove_databases_failures",
            classmethod(_drifted),
        ):
            with pytest.raises(RuntimeError, match="upstream body"):
                _django_patches.apply()
        # ``apply()`` raised during validation, before the install step.
        assert _django_patches._patch_is_installed() is False
    finally:
        SimpleTestCase._remove_databases_failures = saved


def test_apply_fails_loudly_when_upstream_source_is_unavailable():
    """An unreadable captured original is treated as drift, not approved.

    ``inspect.getsource`` raises ``OSError`` for a function with no
    retrievable source file (built here via ``exec``, the shape a
    bytecode-only Django distribution would present). The validator
    must refuse to supersede a body it cannot verify.
    """
    namespace = {}
    exec("def _sourceless(cls):\n    pass\n", namespace)

    with mock.patch.object(
        _django_patches,
        "_original_remove_databases_failures",
        classmethod(namespace["_sourceless"]),
    ):
        with pytest.raises(RuntimeError, match="upstream body"):
            _django_patches.apply()


def test_apply_no_ops_when_toggle_disabled(settings):
    """``APPLY_UPSTREAM_PATCHES = False`` makes ``apply()`` decline to install.

    The Trac #37064 patch is gated by the same flag as the package's
    other upstream patches, so a consumer who opts out of all
    monkey-patching gets none of them. ``apply()`` must return before
    re-installing when the flag is off, and resume installing when it
    is back on.
    """
    saved = SimpleTestCase.__dict__["_remove_databases_failures"]
    try:

        def _foreign(cls):
            pass

        SimpleTestCase._remove_databases_failures = classmethod(_foreign)
        assert _django_patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": False}
        _django_patches.apply()
        assert _django_patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": True}
        _django_patches.apply()
        assert _django_patches._patch_is_installed() is True
    finally:
        SimpleTestCase._remove_databases_failures = saved


def test_apply_no_ops_when_django_dependency_opted_out(settings):
    """``{"APPLY_UPSTREAM_PATCHES": {"django": False}}`` disables only this module.

    The per-dependency escape (rev-apps.md Medium 2, owned by rev-conf.md):
    a mapping naming ``"django"`` makes this ``apply()`` decline to install,
    while a mapping naming only a SIBLING dependency leaves this module
    installing normally (each gate reads its own name).
    """
    saved = SimpleTestCase.__dict__["_remove_databases_failures"]
    try:

        def _foreign(cls):
            pass

        SimpleTestCase._remove_databases_failures = classmethod(_foreign)
        assert _django_patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": False}}
        _django_patches.apply()
        assert _django_patches._patch_is_installed() is False

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"strawberry": False}}
        _django_patches.apply()
        assert _django_patches._patch_is_installed() is True
    finally:
        SimpleTestCase._remove_databases_failures = saved


def test_django_dependency_opt_out_silences_drifted_pin_abort(settings):
    """The inherited escape-hatch coupling, resolved end to end.

    A drifted upstream body pin aborts ``apply()`` with a ``RuntimeError``
    whose text names the per-dependency escape - the exact surface where the
    trap fires on a consumer upgrading Django ahead of the package - and
    setting ``{"django": False}`` then silences the abort (the gate precedes
    validation) without requiring the all-or-nothing global ``False`` that
    would also drop the production request hardening.
    """
    with mock.patch.object(
        _django_patches,
        "_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE",
        "def drifted(): ...\n",
    ):
        settings.DJANGO_STRAWBERRY_FRAMEWORK = {}
        with pytest.raises(RuntimeError, match=r'\{"django": False\}'):
            _django_patches.apply()

        settings.DJANGO_STRAWBERRY_FRAMEWORK = {"APPLY_UPSTREAM_PATCHES": {"django": False}}
        _django_patches.apply()  # gated off per-dependency: no raise, no install attempt
