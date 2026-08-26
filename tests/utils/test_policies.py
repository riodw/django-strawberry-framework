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

from dataclasses import dataclass

import pytest

from django_strawberry_framework.exceptions import ConfigurationError
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
