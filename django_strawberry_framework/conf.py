"""Library settings.

User-provided settings live in a top-level Django settings dict named
``DJANGO_STRAWBERRY_FRAMEWORK``.  Access them via the module-level
``settings`` instance::

    from django_strawberry_framework.conf import settings
    settings.SOME_KEY

Missing keys raise ``AttributeError``.  Whenever Django's
``setting_changed`` signal fires (for example, in tests using
``pytest-django``'s ``settings`` fixture), the singleton ``settings``
instance is mutated in place — the module global is *not* rebound — so
references bound via ``from .conf import settings`` see the change
immediately.

Defensive ``None`` stance (package-wide). Two top-level
consumer-input seams coerce ``None`` (and the missing-key case) to an
empty mapping rather than raising: ``DJANGO_STRAWBERRY_FRAMEWORK =
None`` (this module, treated as "no settings configured") and
``Meta.optimizer_hints = None`` in ``types/base.py`` (treated as "no
hints configured"). Both behave identically to omitting the value
entirely. Tightening the ``None`` cases to raise is tracked as
future-slice work; until then the empty-mapping coercion is the
documented contract for ``None``. *Other* invalid shapes are no longer
defensively coerced here: a non-mapping ``DJANGO_STRAWBERRY_FRAMEWORK``
value raises ``ConfigurationError`` through
``_normalize_user_settings`` before attribute lookup, rather than the
old ``or {}`` collapse that silently absorbed every falsy value.
Reflective shape reads off Strawberry / graphql-core / Django
descriptors (``getattr(obj, name, None) or {}`` and friends in the
optimizer subpackage) are a *separate* case — there the upstream
contract genuinely allows the attribute to be absent or ``None`` on
legitimate shapes, and coercion is unconditionally correct. Do not
unify the two.
"""

from collections.abc import Mapping
from typing import Any

from django.conf import settings as django_settings
from django.test.signals import setting_changed

from django_strawberry_framework.exceptions import ConfigurationError

DJANGO_SETTINGS_KEY = "DJANGO_STRAWBERRY_FRAMEWORK"
_DISPATCH_UID = "django_strawberry_framework.conf.reload_settings"


def _normalize_user_settings(value: Any) -> dict[str, Any]:
    """Validate and normalize a ``DJANGO_STRAWBERRY_FRAMEWORK`` candidate.

    Branches:

    - ``value is None`` -> ``{}``. ``None`` and the missing-key case
      are the package's documented "no settings configured" shape;
      matches the module-level ``None`` stance.
    - Non-``Mapping`` value -> ``ConfigurationError`` naming the
      received type. Protects ``Settings.__getattr__`` from raising a
      bare ``TypeError`` on subscript when a consumer assigns a string
      / list / other non-mapping by mistake, which the pre-fix ``or
      {}`` fallback silently absorbed.
    - ``dict`` -> returned as-is (fast path; preserves identity so
      tests that capture the same dict by reference observe their
      mutations).
    - Other ``Mapping`` instances -> copied into a plain ``dict`` so
      the cache always exposes a uniform ``dict[str, Any]`` shape to
      ``Settings.user_settings`` consumers.

    Shared by ``Settings.__init__`` (eager construction),
    ``Settings.user_settings`` (lazy read from ``django.conf.settings``),
    and ``Settings.reload`` (signal-driven and direct cache replacement)
    so a single shape contract applies across every cache write site.
    """
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ConfigurationError(
            f"`{DJANGO_SETTINGS_KEY}` must be a mapping or None; got {type(value).__name__}.",
        )
    if isinstance(value, dict):
        return value
    return dict(value)


class Settings:
    """Attribute-style accessor for user-provided library settings."""

    def __init__(self, user_settings: Mapping[str, Any] | None = None) -> None:
        """Build a ``Settings`` instance.

        ``None`` (the default) defers loading until first attribute access, at
        which point the value is read from ``django.conf.settings``.  Passing
        a mapping skips the lazy read; ``dict`` values are retained and other
        mappings are copied into a plain ``dict``.  Non-mapping values raise
        ``ConfigurationError`` so malformed configuration fails at
        construction rather than at attribute lookup, matching the
        ``user_settings`` and ``reload`` write sites.
        """
        self._user_settings = None if user_settings is None else _normalize_user_settings(user_settings)

    @property
    def user_settings(self) -> dict[str, Any]:
        """Lazily load user-defined settings from ``django.conf.settings``.

        Missing or ``None`` top-level configuration is treated the same as an
        empty mapping.  Non-mapping values raise ``ConfigurationError`` so
        malformed configuration fails before attribute lookup.

        Not thread-safe; the lazy-load check-and-set and any concurrent
        ``reload_settings`` signal must not race.  Django's
        ``setting_changed`` signal is test-only, so this is satisfied by
        Django's test conventions (single-threaded ``override_settings``
        and ``pytest-django`` ``settings`` fixture usage).
        """
        if self._user_settings is None:
            self._user_settings = _normalize_user_settings(
                getattr(django_settings, DJANGO_SETTINGS_KEY, None),
            )
        return self._user_settings

    def reload(self, value: Mapping[str, Any] | None) -> None:
        """Replace the cached user-settings mapping in place.

        ``None`` restores lazy reload on next attribute access.  Mapping
        values replace the cached settings; ``dict`` instances are retained,
        and other mappings are copied into a plain ``dict``.
        """
        self._user_settings = None if value is None else _normalize_user_settings(value)

    def __getattr__(self, name: str) -> Any:
        """Retrieve a setting's value using attribute-style access.

        Dunder names short-circuit with a plain ``AttributeError`` so
        introspection tools (``copy``, ``deepcopy``, ``inspect``) get
        readable traces instead of the "Invalid setting" message.

        Only ``KeyError`` is caught and converted to ``AttributeError``; a
        malformed ``DJANGO_STRAWBERRY_FRAMEWORK`` value (non-mapping) makes
        the lazy ``self.user_settings`` read raise ``ConfigurationError``,
        which propagates through ``hasattr`` and ``getattr(default=...)``
        probes by design — bad configuration should fail loud rather than
        masquerade as a missing attribute.
        """
        if name.startswith("__"):
            raise AttributeError(name)
        try:
            # ``self.user_settings`` is a descriptor (``@property``), not a
            # ``__getattr__``-driven lookup; keep it a ``@property`` to avoid
            # recursive lookup on malformed config raising
            # ``ConfigurationError`` inside this handler.
            return self.user_settings[name]
        except KeyError:
            raise AttributeError(f"Invalid setting: `{name}`") from None


settings = Settings(None)


def reload_settings(setting: str, value: Any, **kwargs: Any) -> None:
    """Refresh the singleton ``settings`` instance when our key changes.

    Mutates the existing ``Settings`` object instead of rebinding the module
    global so callers that did ``from .conf import settings`` keep seeing
    fresh values.  ``value`` is whatever Django's ``setting_changed`` signal
    sends; ``None`` (e.g. when an ``override_settings`` block exits) restores
    lazy reload on next attribute access.
    """
    if setting == DJANGO_SETTINGS_KEY:
        settings.reload(value)


# Import-time side effect: install the signal receiver so test overrides take
# effect without requiring an AppConfig.ready() hook.  Consumers may import
# ``conf`` before app loading during test bootstrap, so AppConfig.ready() is
# not a viable home for this wiring.  ``dispatch_uid`` makes the connect
# idempotent if the module is ever re-imported under a different name.
setting_changed.connect(reload_settings, dispatch_uid=_DISPATCH_UID)
