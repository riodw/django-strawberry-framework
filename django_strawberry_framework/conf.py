"""Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.

User-provided settings live in a top-level Django settings dict named
``DJANGO_STRAWBERRY_FRAMEWORK``.  Access them via the module-level
``settings`` instance::

    from django_strawberry_framework.conf import settings
    settings.SOME_KEY

Missing keys raise ``AttributeError``.  Whenever Django's
``setting_changed`` signal fires (for example, in tests using
``pytest-django``'s ``settings`` fixture), the singleton ``settings``
instance is mutated in place - the module global is *not* rebound - so
references bound via ``from .conf import settings`` see the change
immediately.  The singleton is also live-synced against
``django.conf.settings``: if the key is deleted or replaced without a
signal (pytest-django's ``del settings.DJANGO_STRAWBERRY_FRAMEWORK``
deletes without emitting ``setting_changed``), the next read rebuilds
from the live value instead of keeping a stale cache.

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
optimizer subpackage) are a *separate* case - there the upstream
contract genuinely allows the attribute to be absent or ``None`` on
legitimate shapes, and coercion is unconditionally correct. Do not
unify the two.
"""

from collections.abc import Callable, Mapping
from typing import Any

from django.conf import settings as django_settings
from django.test.signals import setting_changed

from django_strawberry_framework.exceptions import ConfigurationError

DJANGO_SETTINGS_KEY = "DJANGO_STRAWBERRY_FRAMEWORK"
_DISPATCH_UID = "django_strawberry_framework.conf.reload_settings"

# Toggle for the defensive patches the package ships for upstream bugs
# (see ``_django_patches`` / ``_strawberry_patches`` / ``_cross_web_patches``).
# Accepts a ``bool`` (the global toggle) or a ``Mapping[str, bool]`` keyed by
# ``UPSTREAM_PATCH_DEPENDENCIES`` names (per-dependency opt-out; missing names
# stay enabled). Opt-out: defaults to ``True`` so consumers get the fixes
# automatically, matching the "no opt-in boilerplate" stance of the patch
# modules. See ``upstream_patches_enabled`` for the full shape contract.
APPLY_UPSTREAM_PATCHES_KEY = "APPLY_UPSTREAM_PATCHES"

# Canonical ``APPLY_UPSTREAM_PATCHES`` mapping keys - one name per patch
# module, matching the package's one-module-per-dependency organizing rule.
# ``strawberry`` and ``cross_web`` jointly own one fix (the malformed-body
# ``400`` hardening: the Strawberry patch hardens both transports' body
# parse, the cross_web patch routes the sync transport's bytes into it), so
# disabling one of the pair alone is safe but leaves the sync transport
# unfixed.
UPSTREAM_PATCH_DEPENDENCIES = frozenset({"django", "strawberry", "cross_web"})

# Default nested-connection fetch strategy for ``DjangoOptimizerExtension``
# instances constructed without an explicit ``nested_connection_strategy=``
# (see ``optimizer/nested_fetch.py``). Defaults to ``"windowed"``.
NESTED_CONNECTION_STRATEGY_KEY = "NESTED_CONNECTION_STRATEGY"

# Project-wide GraphQL endpoint for the ``testing/client.py`` test-client
# family (``TestClient`` / ``AsyncTestClient`` / ``GraphQLTestMixin``) -
# graphene-django's ``TESTING_ENDPOINT`` knob, package-namespaced (spec-043
# Decision 7). Defaults to ``"/graphql/"`` (trailing slash - fakeshop's
# mount, Strawberry's own base default, and Django's ``APPEND_SLASH``
# convention; graphene's slash-less ``"/graphql"`` is a documented
# non-borrow).
TESTING_ENDPOINT_KEY = "TESTING_ENDPOINT"

# Whether generated filter inputs hide the flat relational traversal fields
# (``categoryName``, deep ``entriesPropertyCategoryName``, ...) in favor of
# the nested ``RelatedFilter`` branches alone (see
# ``filters/inputs.py::_build_input_fields``). Defaults to ``False`` - both
# shapes emitted (graphene-django parity; matches
# ``django-graphene-filters``'s default).
HIDE_FLAT_FILTERS_KEY = "HIDE_FLAT_FILTERS"

# Schema-wide default GlobalID type-name-slot strategy for Relay-Node-shaped
# types without a per-type ``Meta.globalid_strategy`` (spec-031 Decision 5;
# see ``types/relay.py::_resolve_globalid_strategy``, which validates the
# value where the strategy vocabulary lives). Defaults to ``None`` - no
# schema-wide override; the ``DEFAULT_GLOBALID_STRATEGY`` package default
# applies downstream.
RELAY_GLOBALID_STRATEGY_KEY = "RELAY_GLOBALID_STRATEGY"


# Sentinel for "no live ``django.conf.settings`` object has been bound yet"
# (distinct from ``None``, which is a valid live value meaning "no settings").
_LIVE_UNSET: Any = object()


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

        Explicit mappings are *not* django-backed: they keep the supplied
        cache regardless of ``django.conf.settings``.  The module singleton
        (constructed with ``None``) and any instance that later ``reload``s
        to ``None`` are django-backed and re-sync when the live setting
        object changes without a ``setting_changed`` notification (notably
        ``del settings.DJANGO_STRAWBERRY_FRAMEWORK`` via pytest-django,
        which deletes the key without emitting the signal).
        """
        if user_settings is None:
            self._user_settings: dict[str, Any] | None = None
            self._live_source: Any = _LIVE_UNSET
            self._django_backed = True
        else:
            self._user_settings = _normalize_user_settings(user_settings)
            self._live_source = _LIVE_UNSET
            self._django_backed = False

    @property
    def user_settings(self) -> dict[str, Any]:
        """Lazily load user-defined settings from ``django.conf.settings``.

        Missing or ``None`` top-level configuration is treated the same as an
        empty mapping.  Non-mapping values raise ``ConfigurationError`` so
        malformed configuration fails before attribute lookup.

        Django-backed instances (the module singleton, or any instance after
        ``reload(None)``) re-check the live ``django.conf.settings`` object
        on every access.  When it is still the same object the cache was
        built from, the cached ``dict`` is returned (preserving identity for
        in-place mutations).  When the live object has been replaced or the
        key deleted without ``setting_changed`` (pytest-django's ``del
        settings.DJANGO_STRAWBERRY_FRAMEWORK``), the cache is rebuilt from
        the live value so readers never keep serving a stale mapping.

        Explicit ``Settings(mapping)`` instances are not django-backed and
        return their fixed cache.

        Not thread-safe; the lazy-load check-and-set and any concurrent
        ``reload_settings`` signal must not race.  Django's
        ``setting_changed`` signal is test-only, so this is satisfied by
        Django's test conventions (single-threaded ``override_settings``
        and ``pytest-django`` ``settings`` fixture usage).
        """
        if not self._django_backed:
            # Explicit construction / non-``None`` reload on a non-backed
            # instance always leaves a concrete mapping in the cache.
            cached = self._user_settings
            if cached is None:  # pragma: no cover - invariant of non-backed init/reload
                raise RuntimeError("non-django-backed Settings cache missing")
            return cached

        live = getattr(django_settings, DJANGO_SETTINGS_KEY, None)
        if self._user_settings is not None and live is self._live_source:
            return self._user_settings
        # Normalize BEFORE binding ``_live_source``: a rejected live shape must
        # leave the prior pointer intact so the next access retries (and fails
        # loud again) instead of treating the bad live object as a successful
        # cache key and returning the stale prior mapping.
        normalized = _normalize_user_settings(live)
        self._live_source = live
        self._user_settings = normalized
        return self._user_settings

    def reload(self, value: Mapping[str, Any] | None) -> None:
        """Replace the cached user-settings mapping in place.

        ``None`` restores django-backed lazy reload on next attribute access.
        Mapping values replace the cached settings; ``dict`` instances are
        retained, and other mappings are copied into a plain ``dict``.  The
        live-source pointer tracks ``value`` itself (pre-normalization) so a
        subsequent django-backed read can keep the cache when
        ``django.conf.settings`` still holds that same object.
        """
        if value is None:
            self._user_settings = None
            self._live_source = _LIVE_UNSET
            self._django_backed = True
            return
        self._user_settings = _normalize_user_settings(value)
        self._live_source = value

    def __getattr__(self, name: str) -> Any:
        """Retrieve a setting's value using attribute-style access.

        Dunder names short-circuit with a plain ``AttributeError`` so
        introspection tools (``copy``, ``deepcopy``, ``inspect``) get
        readable traces instead of the "Invalid setting" message.

        Only ``KeyError`` is caught and converted to ``AttributeError``; a
        malformed ``DJANGO_STRAWBERRY_FRAMEWORK`` value (non-mapping) makes
        the lazy ``self.user_settings`` read raise ``ConfigurationError``,
        which propagates through ``hasattr`` and ``getattr(default=...)``
        probes by design - bad configuration should fail loud rather than
        masquerade as a missing attribute.
        """
        if name in {
            "user_settings",
            "_user_settings",
            "_live_source",
            "_django_backed",
        } or name.startswith("__"):
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


def upstream_patches_enabled(dependency: str) -> bool:
    """Whether ``dependency``'s upstream defensive patches apply at app load.

    Reads ``DJANGO_STRAWBERRY_FRAMEWORK["APPLY_UPSTREAM_PATCHES"]``,
    defaulting to ``True`` when the key (or the whole settings dict) is
    absent. Two configured shapes are accepted:

    - ``bool`` - the global toggle: ``False`` stops the framework from
      monkey-patching any of its upstream dependencies (Django,
      Strawberry, and ``cross_web``) at startup.
    - ``Mapping[str, bool]`` keyed by ``UPSTREAM_PATCH_DEPENDENCIES``
      names - per-dependency opt-out: ``{"django": False}`` disables
      only the test-only Django teardown patch while the production
      request-hardening patches (``strawberry`` / ``cross_web``) stay
      installed. Missing names default to ``True`` (the opt-out stance
      holds per dependency). ``strawberry`` and ``cross_web`` jointly
      own the malformed-body hardening - see the
      ``UPSTREAM_PATCH_DEPENDENCIES`` comment.

    Any other shape raises ``ConfigurationError`` (the
    ``_normalize_user_settings`` fail-loud precedent): a non-bool /
    non-mapping value (a ``"false"`` string is truthy and would silently
    ENABLE the patches under bool coercion), a non-string mapping key
    (dependency names are strings; anything else is a wrong shape, not a
    candidate name), an unknown mapping name (a typo'd name must not
    silently keep patching), or a non-bool mapping value (``{"django":
    "false"}`` would silently invert intent). The whole mapping is
    validated on every read, not just ``dependency``'s entry, so a typo
    fails loud at the first gate regardless of which patch module reads
    first.

    Internal API (not exported from the package ``__init__``): the only
    callers are the three patch modules' ``apply()`` gates, each passing
    its own canonical name. A ``dependency`` outside
    ``UPSTREAM_PATCH_DEPENDENCIES`` raises ``ValueError`` so the
    constant and the gate call sites cannot drift apart.

    Read once per patch ``apply()`` (i.e. at app load). A *malformed*
    (non-mapping) ``DJANGO_STRAWBERRY_FRAMEWORK`` value still fails loud
    via the ``ConfigurationError`` path shared by every setting read -
    only a missing key falls back to the default.
    """
    if dependency not in UPSTREAM_PATCH_DEPENDENCIES:
        raise ValueError(
            f"upstream_patches_enabled() got unknown dependency {dependency!r}; add new "
            "patch-module names to UPSTREAM_PATCH_DEPENDENCIES so consumers can opt out.",
        )
    configured = getattr(settings, APPLY_UPSTREAM_PATCHES_KEY, True)
    if isinstance(configured, bool):
        return configured
    if isinstance(configured, Mapping):
        # Key-type guard FIRST so a non-string key never reaches the
        # unknown-name framing below, whose ``sorted()`` would leak a bare
        # ``TypeError`` on mixed unorderable key types instead of the
        # promised ``ConfigurationError`` (the
        # ``types/base.py::_validate_relation_shapes`` key-guard precedent).
        for name in configured:
            if not isinstance(name, str):
                raise ConfigurationError(
                    f"`{APPLY_UPSTREAM_PATCHES_KEY}` keys must be dependency name strings; "
                    f"got {name!r}.",
                )
        unknown = set(configured) - UPSTREAM_PATCH_DEPENDENCIES
        if unknown:
            raise ConfigurationError(
                f"`{APPLY_UPSTREAM_PATCHES_KEY}` names unknown patch dependencies "
                f"{sorted(unknown)}; valid names are {sorted(UPSTREAM_PATCH_DEPENDENCIES)}.",
            )
        for name, value in configured.items():
            if not isinstance(value, bool):
                raise ConfigurationError(
                    f"`{APPLY_UPSTREAM_PATCHES_KEY}[{name!r}]` must be a bool; "
                    f"got {type(value).__name__}.",
                )
        return configured.get(dependency, True)
    raise ConfigurationError(
        f"`{APPLY_UPSTREAM_PATCHES_KEY}` must be a bool or a mapping of dependency names "
        f"to bools; got {type(configured).__name__}.",
    )


def nested_connection_strategy_setting() -> str:
    """The configured default nested-connection fetch strategy name.

    Reads ``DJANGO_STRAWBERRY_FRAMEWORK["NESTED_CONNECTION_STRATEGY"]``,
    defaulting to ``"windowed"`` when the key (or the whole settings dict)
    is absent. Consumed by ``optimizer/nested_fetch.py::resolve_strategy``
    at ``DjangoOptimizerExtension`` construction; validation (unknown-name
    ``ConfigurationError``) happens there, where the strategy registry
    lives.
    """
    return getattr(settings, NESTED_CONNECTION_STRATEGY_KEY, "windowed")


def testing_endpoint_setting() -> str:
    """The configured project-wide GraphQL endpoint for the test-client family.

    Reads ``DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]``, defaulting to
    ``"/graphql/"`` when the key (or the whole settings dict) is absent.
    Consumed by ``testing/client.py`` at ``TestClient`` construction and per
    ``GraphQLTestMixin.query()`` call, as the lowest rungs of the endpoint
    precedence ladder (per-call ``url=`` > constructor ``path=`` > class-attr
    ``GRAPHQL_URL`` > this setting > default). No validation beyond the shared
    malformed-dict guard: a wrong endpoint string surfaces as an ordinary 404
    at request time, where the failure names the actual response.
    """
    return getattr(settings, TESTING_ENDPOINT_KEY, "/graphql/")


# Pytest collection guard: the reader's name matches pytest's default
# ``test*`` function pattern, so a test module importing it UNALIASED gets it
# collected as a test; it returns a ``str``, which fails the run via
# ``PytestReturnNotNoneWarning`` under a ``filterwarnings = error`` posture.
# Same hazard class (and same idiom) as ``testing/client.py::TestClient``'s
# class-level guard.
testing_endpoint_setting.__test__ = False


def hide_flat_filters_setting() -> bool:
    """Whether generated filter inputs hide the flat relational traversal fields.

    Reads ``DJANGO_STRAWBERRY_FRAMEWORK["HIDE_FLAT_FILTERS"]``, defaulting to
    ``False`` when the key (or the whole settings dict) is absent. Consumed by
    ``filters/inputs.py::_build_input_fields`` at input-class build time,
    which owns the truthiness coercion and the skip semantics (hidden flat
    paths remain reachable through their nested ``RelatedFilter`` branch).
    """
    return getattr(settings, HIDE_FLAT_FILTERS_KEY, False)


def relay_globalid_strategy_setting() -> str | Callable[..., str] | None:
    """The configured schema-wide GlobalID type-name-slot strategy (or ``None``).

    Reads ``DJANGO_STRAWBERRY_FRAMEWORK["RELAY_GLOBALID_STRATEGY"]``,
    defaulting to ``None`` ("no schema-wide override") when the key (or the
    whole settings dict) is absent. Consumed by
    ``types/relay.py::_resolve_globalid_strategy`` at finalization, where the
    value is validated through the shared ``_validate_globalid_strategy``
    rule - ``conf.py`` stays a thin reader that does not validate domain
    values.
    """
    return getattr(settings, RELAY_GLOBALID_STRATEGY_KEY, None)


def reload_settings(setting: str, value: Any, **kwargs: Any) -> None:
    """Refresh the singleton ``settings`` instance when our key changes.

    Mutates the existing ``Settings`` object instead of rebinding the module
    global so callers that did ``from .conf import settings`` keep seeing
    fresh values.  ``value`` is whatever Django's ``setting_changed`` signal
    sends; ``None`` (e.g. when an ``override_settings`` block exits) restores
    lazy reload on next attribute access.  ``**kwargs`` absorbs the remaining
    ``setting_changed`` payload (``enter``, ``sender``, ``signal``) so the
    receiver matches the signal signature; it is required, not optional.
    """
    if setting == DJANGO_SETTINGS_KEY:
        settings.reload(value)


# Import-time side effect: install the signal receiver so test overrides take
# effect without requiring an AppConfig.ready() hook.  Consumers may import
# ``conf`` before app loading during test bootstrap, so AppConfig.ready() is
# not a viable home for this wiring.  ``dispatch_uid`` makes the connect
# idempotent if the module is ever re-imported under a different name.
setting_changed.connect(reload_settings, dispatch_uid=_DISPATCH_UID)
