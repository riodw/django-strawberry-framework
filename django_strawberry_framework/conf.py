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

Defensive-coerce stance (package-wide). Two top-level consumer-input
seams currently coerce ``None`` to an empty mapping rather than
raising: ``DJANGO_STRAWBERRY_FRAMEWORK = None`` (this module, treated
as "no settings configured") and ``Meta.optimizer_hints = None`` in
``types/base.py`` (treated as "no hints configured"). Both behave
identically to omitting the value entirely. Tightening either to
raise a configuration error is tracked as future-slice work; until
then the empty-mapping coercion is the documented contract. Reflective
shape reads off Strawberry / graphql-core / Django descriptors
(``getattr(obj, name, None) or {}`` and friends in the optimizer
subpackage) are a *separate* case — there the upstream contract
genuinely allows the attribute to be absent or ``None`` on legitimate
shapes, and coercion is unconditionally correct. Do not unify the two.
"""

from typing import Any

from django.conf import settings as django_settings
from django.test.signals import setting_changed

DJANGO_SETTINGS_KEY = "DJANGO_STRAWBERRY_FRAMEWORK"
_DISPATCH_UID = "django_strawberry_framework.conf.reload_settings"


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
        """Lazily load user-defined settings from ``django.conf.settings``.

        A falsy value (``None``, missing key, empty dict) collapses to an
        empty dict so attribute access uniformly raises ``AttributeError``
        for unknown keys rather than ``TypeError`` on ``None`` subscript.
        """
        if self._user_settings is None:
            self._user_settings = getattr(django_settings, DJANGO_SETTINGS_KEY, {}) or {}
        return self._user_settings

    def reload(self, value: dict[str, Any] | None) -> None:
        """Replace the cached user-settings mapping in place.

        ``None`` restores lazy reload on next attribute access; any other
        value is used as-is.
        """
        self._user_settings = value

    def __getattr__(self, name: str) -> Any:
        """Retrieve a setting's value using attribute-style access.

        Dunder names short-circuit with a plain ``AttributeError`` so
        introspection tools (``copy``, ``deepcopy``, ``inspect``) get
        readable traces instead of the "Invalid setting" message.
        """
        if name.startswith("__"):
            raise AttributeError(name)
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
        settings.reload(value)


# Import-time side effect: install the signal receiver so test overrides take
# effect without requiring an AppConfig.ready() hook.  Consumers may import
# ``conf`` before app loading during test bootstrap, so AppConfig.ready() is
# not a viable home for this wiring.  ``dispatch_uid`` makes the connect
# idempotent if the module is ever re-imported under a different name.
setting_changed.connect(reload_settings, dispatch_uid=_DISPATCH_UID)
