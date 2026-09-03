"""``utils/policies.py::resolve_policy`` - the shared schema-construction resolver.

The generic contract that ``resource_policy.py::resolve_resource_policy`` and
``error_policy.py::resolve_error_policy`` both delegate to, exercised directly
with probe policies so the precedence ladder, the mapping-type gate, the
unknown-key vocabulary message, and the derived article are pinned once here.
Each flavor's own tier (``tests/test_resource_policy.py``,
``tests/test_error_policy.py``, plus the live ``/graphql/`` rows) pins its
wire-visible wording end to end.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pytest

from django_strawberry_framework.error_policy import resolve_error_policy
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.resource_policy import resolve_resource_policy
from django_strawberry_framework.utils.policies import resolve_policy


@dataclass(frozen=True)
class _ProbePolicy:
    width: int = 10


_PROBE_DEFAULT = _ProbePolicy()


def _resolve(explicit: object = None, setting: object = None) -> _ProbePolicy:
    return resolve_policy(
        explicit,
        policy_cls=_ProbePolicy,
        default=_PROBE_DEFAULT,
        read_setting=(lambda: setting),
        display_name="probe policy",
        unit="bound",
    )


def test_an_explicit_instance_passes_through_untouched():
    """A constructed policy already validated itself; identity is preserved."""
    policy = _ProbePolicy(width=3)
    assert _resolve(policy) is policy


def test_no_source_at_all_resolves_to_the_default():
    assert _resolve(None, None) is _PROBE_DEFAULT


def test_an_instance_through_the_setting_slot_passes_through_untouched():
    """A validated instance behind the setting slot is the same trusted declaration.

    The explicit argument and the setting read are two spellings of one
    override source, so an instance from either passes through unchanged;
    rejecting the setting spelling made the typed message name the policy class
    as the received type while claiming it must be one.
    """
    policy = _ProbePolicy(width=3)
    assert _resolve(None, policy) is policy


def test_the_setting_supplies_overrides_when_the_argument_is_absent():
    assert _resolve(None, {"width": 4}) == _ProbePolicy(width=4)


def test_an_explicit_mapping_outranks_the_setting():
    assert _resolve({"width": 9}, {"width": 4}) == _ProbePolicy(width=9)


def test_a_non_mapping_override_is_rejected_with_the_derived_article():
    with pytest.raises(ConfigurationError, match="must be a _ProbePolicy or a mapping"):
        _resolve(12)


def test_unknown_keys_are_rejected_naming_the_valid_vocabulary():
    with pytest.raises(ConfigurationError, match=r"Unknown probe-policy bound\(s\): wirth"):
        _resolve({"wirth": 1})


# ---------------------------------------------------------------------------
# Hostile override mappings: one materialization, typed containment (both flavors)
# ---------------------------------------------------------------------------


class _DivergentMapping(Mapping):
    """A stateful Mapping that yields a different key set on every full iteration."""

    def __init__(self, passes: list[list[tuple[str, object]]]) -> None:
        self._passes = [dict(pass_) for pass_ in passes]
        self._current: dict[str, object] = {}

    def __iter__(self):
        self._current = self._passes.pop(0) if self._passes else {}
        return iter(self._current)

    def __getitem__(self, key):
        return self._current[key]

    def __len__(self):
        return len(self._current)


class _UnhashableKeyMapping(Mapping):
    def __iter__(self):
        return iter((["k"],))

    def __getitem__(self, key):
        return 1

    def __len__(self):
        return 1


class _RaisingIterMapping(Mapping):
    def __iter__(self):
        raise RuntimeError("hostile __iter__")

    def __getitem__(self, key):
        return 1

    def __len__(self):
        return 1


_FLAVORS = [
    pytest.param(resolve_error_policy, "message", "From hostile mapping.", id="error-policy"),
    pytest.param(resolve_resource_policy, "max_page_size", 20, id="resource-policy"),
]


@pytest.mark.parametrize(("resolver", "key", "value"), _FLAVORS)
def test_a_divergent_one_shot_mapping_resolves_from_one_consumed_pass(resolver, key, value):
    """The mapping is consumed ONCE: pass 2 can no longer smuggle unknown keys.

    The pre-fix resolver validated unknown keys over one iteration and then
    expanded the same mapping again for ``policy_cls(**dict(overrides))``, so a
    mapping whose second pass yielded ``bogus`` escaped the typed unknown-key
    rejection as a raw ``TypeError: ErrorPolicy.__init__() got an unexpected
    keyword argument 'bogus'``. One materialization makes pass 1 authoritative.
    """
    policy = resolver(_DivergentMapping([[(key, value)], [("bogus", 1), ("x", 1)]]))
    assert getattr(policy, key) == value


@pytest.mark.parametrize(
    "resolver",
    [row.values[0] for row in _FLAVORS],
    ids=["error-policy", "resource-policy"],
)
def test_an_unhashable_key_is_typed_rejected_not_a_bare_typeerror(resolver):
    with pytest.raises(ConfigurationError, match="must be strings|iteration failed"):
        resolver(_UnhashableKeyMapping())


@pytest.mark.parametrize(
    "resolver",
    [row.values[0] for row in _FLAVORS],
    ids=["error-policy", "resource-policy"],
)
def test_a_raising_iterator_is_typed_rejected_not_leaked(resolver):
    with pytest.raises(ConfigurationError, match="iteration failed"):
        resolver(_RaisingIterMapping())


class _TypedRaisingMapping(Mapping):
    """A Mapping whose own materialization read fails with the typed error."""

    def __iter__(self):
        raise ConfigurationError("hostile keys read")

    def __getitem__(self, key):
        return 1

    def __len__(self):
        return 1


@pytest.mark.parametrize(
    "resolver",
    [row.values[0] for row in _FLAVORS],
    ids=["error-policy", "resource-policy"],
)
def test_a_configuration_error_from_materialization_propagates_unchanged(resolver):
    """A ``ConfigurationError`` escaping ``dict(overrides)`` is re-raised verbatim.

    Materialization is a consumption point like any other: a typed rejection
    from the mapping's own reads is the honest verdict and must reach the
    caller as-is, not degraded to the generic "iteration failed" wording that
    the raw-failure arm reserves for untyped exceptions.
    """
    with pytest.raises(ConfigurationError, match="hostile keys read"):
        resolver(_TypedRaisingMapping())


@pytest.mark.parametrize(
    "resolver",
    [row.values[0] for row in _FLAVORS],
    ids=["error-policy", "resource-policy"],
)
def test_a_hashable_non_string_key_is_typed_rejected_at_the_key_guard(resolver):
    """A hashable non-string override key still reaches the key-type guard.

    An unhashable key dies inside ``dict()`` materialization (the "iteration
    failed" arm); a HASHABLE non-string key materializes fine and must reach
    the ``must be strings`` rejection, not a bare ``TypeError`` from set
    membership or ``sorted()`` over mixed keys.
    """
    with pytest.raises(ConfigurationError, match="must be strings"):
        resolver({42: 1})
