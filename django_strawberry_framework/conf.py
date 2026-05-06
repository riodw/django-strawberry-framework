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
"""

from typing import Any

from django.conf import settings as django_settings
from django.test.signals import setting_changed

DJANGO_SETTINGS_KEY = "DJANGO_STRAWBERRY_FRAMEWORK"


class Settings:
    """Attribute-style accessor for user-provided library settings."""

    def __init__(self, user_settings: dict[str, Any] | None = None) -> None:
        """Build a ``Settings`` instance.

        ``None`` (the default) defers loading until first attribute access, at
        which point the value is read from ``django.conf.settings``.  Passing
        a dict uses it as-is and skips the lazy read.
        """
        self._user_settings = user_settings

    @property
    def user_settings(self) -> dict[str, Any]:
        """Lazily load user-defined settings from ``django.conf.settings``."""
        if self._user_settings is None:
            self._user_settings = getattr(django_settings, DJANGO_SETTINGS_KEY, {}) or {}
        return self._user_settings

    def __getattr__(self, name: str) -> Any:
        """Retrieve a setting's value using attribute-style access."""
        try:
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
        settings._user_settings = value


# Import-time side effect: install the signal receiver so test overrides take
# effect without requiring an AppConfig.ready() hook.  Consumers may import
# ``conf`` before app loading during test bootstrap, so AppConfig.ready() is
# not a viable home for this wiring.
setting_changed.connect(reload_settings)
