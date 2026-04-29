"""Library settings.

User-provided settings live in a top-level Django settings dict named
``DJANGO_STRAWBERRY_FRAMEWORK``.  Access them via the module-level
``settings`` instance::

    from django_strawberry_framework.conf import settings
    settings.SOME_KEY

Missing keys raise ``AttributeError``.  Whenever Django's
``setting_changed`` signal fires (for example, in tests using
``pytest-django``'s ``settings`` fixture), the module-level ``settings``
instance is rebuilt so changes are visible immediately.
"""

from typing import Any

from django.conf import settings as django_settings
from django.test.signals import setting_changed

DJANGO_SETTINGS_KEY = "DJANGO_STRAWBERRY_FRAMEWORK"


class Settings:
    """Attribute-style accessor for user-provided library settings."""

    def __init__(self, user_settings: dict[str, Any] | None = None) -> None:
        """Initialize with optional user settings."""
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
    """Rebuild the module-level ``settings`` when our key changes."""
    global settings
    if setting == DJANGO_SETTINGS_KEY:
        settings = Settings(value)


setting_changed.connect(reload_settings)
