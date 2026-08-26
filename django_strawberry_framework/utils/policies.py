"""Shared schema-construction policy normalization.

``resource_policy.py::resolve_resource_policy`` and ``error_policy.py::
resolve_error_policy`` are deliberately the same shape - a consumer who has
learned how one schema-construction policy is configured has learned both -
so that shape lives here once: an explicit policy instance passes through, an
absent one falls back to the configured setting and then to the fail-closed
package default, a non-mapping override is rejected, unknown keys are rejected
naming the valid vocabulary, and a mapping is applied over the dataclass
defaults. Domain validation stays with the policy classes themselves
(``__post_init__``), so an instance from any path was validated on the same
terms.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields
from typing import Any, TypeVar

from ..exceptions import ConfigurationError, describe_value

__all__ = ("resolve_policy",)

PolicyT = TypeVar("PolicyT")


def _article(name: str) -> str:
    """The indefinite article for a class name: "an ErrorPolicy", "a ResourcePolicy"."""
    return "an" if name[0] in "AEIOU" else "a"


def resolve_policy(
    explicit: PolicyT | Mapping[str, Any] | None,
    *,
    policy_cls: type[PolicyT],
    default: PolicyT,
    read_setting: Callable[[], Any],
    display_name: str,
    unit: str,
) -> PolicyT:
    """Normalize one deployment policy the way every schema-construction policy resolves.

    Precedence, highest first: the ``explicit`` argument (a ``policy_cls``
    instance passes through as-is - it has already validated itself), the
    deployment mapping read through ``read_setting``, and ``default``.

    ``display_name`` is the human name used in messages ("resource policy") and
    ``unit`` is what one override key is called there ("bound" / "option"); the
    wire-visible wording of both rejections is produced from these, so the two
    resolvers cannot drift apart in text any more than in behavior.
    """
    if isinstance(explicit, policy_cls):
        return explicit
    overrides = explicit if explicit is not None else read_setting()
    if overrides is None:
        return default
    if not isinstance(overrides, Mapping):
        raise ConfigurationError(
            f"The {display_name} must be {_article(policy_cls.__name__)} "
            f"{policy_cls.__name__} or a mapping of {unit} names to values; "
            f"got {describe_value(overrides)}.",
        )
    known = {field.name for field in fields(policy_cls)}
    unknown = sorted(str(name) for name in overrides if name not in known)
    if unknown:
        raise ConfigurationError(
            f"Unknown {display_name.replace(' ', '-')} {unit}(s): {', '.join(unknown)}. "
            f"Valid {unit}s: {', '.join(sorted(known))}.",
        )
    return policy_cls(**dict(overrides))
