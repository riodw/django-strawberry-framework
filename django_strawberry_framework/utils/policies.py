"""Shared schema-construction policy normalization.

``resource_policy.py::resolve_resource_policy`` and ``error_policy.py::
resolve_error_policy`` are deliberately the same shape - a consumer who has
learned how one schema-construction policy is configured has learned both -
so that shape lives here once: an explicit policy instance is canonicalized into
a private validated duplicate and used, an absent one falls back to the
configured setting and then to the fail-closed package default, a non-mapping
override is rejected, unknown keys are rejected naming the valid vocabulary, and
a mapping is applied over the dataclass defaults. A mapping override is
MATERIALIZED ONCE into a plain ``dict`` before
anything reads it, so validation and construction see the same keys even when
the mapping is stateful, one-shot, or otherwise hostile - a Mapping that
diverges between passes, yields an unhashable key, or raises mid-iteration is
a typed ``ConfigurationError``, never a raw ``TypeError`` / ``RuntimeError``
leaking out of schema construction. Domain validation stays with the policy
classes themselves (``__post_init__``), so an instance from any path was
validated on the same terms.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields
from typing import Any, TypeVar

from ..exceptions import ConfigurationError, describe_value

__all__ = ("canonical_policy", "copy_policy", "resolve_policy")

PolicyT = TypeVar("PolicyT")


def copy_policy(policy: PolicyT) -> PolicyT:
    """Return a private duplicate of ``policy`` that shares no state with it.

    Every surface that hands a policy OUT gives out one of these rather than the
    object an enforcement seam reads: the schema attribute a consumer holds, the
    request-context mirror, and ``resource_policy.py::policy_from_info``. Being a
    frozen dataclass rejects ``setattr``, which guards against the accident; it
    does not stop ``instance.__dict__[name] = value`` or ``object.__setattr__``,
    so frozen is not by itself an authority boundary and is not what keeps a
    resolver from widening its own request. What keeps it is that the object a
    resolver can reach is a duplicate - writing it changes the writer's own copy
    and nothing any bound is read from - and that the authority is reachable
    from no consumer-visible name at all.

    Built by field-dict copy rather than by calling the constructor, because the
    source validated itself when it was built and this runs on the path a
    collection resolver takes: re-validating every bound per read would put a
    schema-construction check on a per-field seam.
    """
    duplicate = object.__new__(type(policy))
    duplicate.__dict__.update(policy.__dict__)
    return duplicate


def canonical_policy(policy: Any, *, policy_cls: type[PolicyT], display_name: str) -> PolicyT:
    """Return a private, validated ``policy_cls`` built from ``policy``'s fields.

    ALWAYS a new object, never the one handed in, and the exact type is not a
    reason to skip the copy. What an enforcement seam reads has to be an object
    no one outside this package holds a reference to: a caller who keeps the
    instance they passed to ``DjangoSchema(resource_policy=...)`` - or who
    leaves one in ``settings`` - still holds the thing every bound would be read
    from, and a frozen dataclass admits ``policy.__dict__[bound] = wider`` by
    the same route the schema attribute does. The copy is what makes a bound
    settled at construction stay settled; the schema is process-lived, so
    without it one write after startup widens every later request.

    The fields are also re-read and re-validated rather than trusted, for two
    reasons that meet here. ``isinstance`` admits a SUBCLASS, whose field reads
    are consumer code: a ``__getattribute__`` or property answering honestly
    while the constructor validates and differently afterwards passes every
    check the class performs on itself and then hands an enforcement seam
    whatever it likes - an ``int`` subclass whose ``__gt__`` raises turns a
    bound comparison into a raw error out of a collection resolver. And an
    EXACT instance's ``__post_init__`` is a statement about the values it was
    built with, never about the ones it carries now. Each field is therefore
    read once, here, and those values build an instance that validates them on
    the ordinary terms; the original is discarded and no seam downstream ever
    calls it again. A read that raises is a typed ``ConfigurationError`` rather
    than a raw error, because this runs at schema construction and a policy
    that cannot be read is a deployment fault.
    """
    values: dict[str, Any] = {}
    reading = ""
    try:
        for field in fields(policy_cls):
            reading = field.name
            values[reading] = getattr(policy, reading)
    except Exception as exc:
        raise ConfigurationError(
            f"The {display_name} could not be read: "
            f"{policy_cls.__name__}.{reading} raised on access.",
        ) from exc
    return policy_cls(**values)


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

    Precedence, highest first: the ``explicit`` argument, the deployment value
    read through ``read_setting``, and ``default``. An instance from either
    override slot is put through :func:`canonical_policy` first, so what the
    schema stores is a private, freshly validated ``policy_cls`` that no caller
    holds a reference to.

    ``display_name`` is the human name used in messages ("resource policy") and
    ``unit`` is what one override key is called there ("bound" / "option"); the
    wire-visible wording of both rejections is produced from these, so the two
    resolvers cannot drift apart in text any more than in behavior.
    """
    if isinstance(explicit, policy_cls):
        return canonical_policy(explicit, policy_cls=policy_cls, display_name=display_name)
    overrides = explicit if explicit is not None else read_setting()
    if overrides is None:
        return default
    if isinstance(overrides, policy_cls):
        # An instance behind the SETTING slot is the same declaration the
        # explicit argument accepts - the two override sources are one ladder
        # with two spellings, so an instance from either is canonicalized on the
        # same terms. (Rejecting it here made the typed message name the policy
        # class as the received type while claiming it must be one.)
        return canonical_policy(overrides, policy_cls=policy_cls, display_name=display_name)
    if not isinstance(overrides, Mapping):
        raise ConfigurationError(
            f"The {display_name} must be {_article(policy_cls.__name__)} "
            f"{policy_cls.__name__} or a mapping of {unit} names to values; "
            f"got {describe_value(overrides)}.",
        )
    # Materialize ONCE, and read only the plain copy afterwards. A ``Mapping``
    # may be stateful: validating unknown keys over one iteration and then
    # calling ``policy_cls(**dict(overrides))`` over a second would let a
    # one-shot generator-style mapping diverge between the two passes - the
    # unknown-key check could pass keys the constructor then rejects (a bare
    # ``TypeError`` instead of the typed rejection) or never see at all. One
    # consumption point is the same hardening ``conf.py::
    # upstream_patches_enabled`` applies to its own settings mapping.
    try:
        plain = dict(overrides)
    except ConfigurationError:
        raise
    except Exception as exc:
        raise ConfigurationError(
            f"The {display_name} is not a valid {unit} mapping; iteration failed.",
        ) from exc
    # Key-type guard FIRST: an unhashable or non-string key must reach this
    # typed rejection, not a bare ``TypeError`` from set membership or a
    # ``sorted()`` over mixed unorderable names (the
    # ``conf.py::upstream_patches_enabled`` key-guard precedent).
    for name in plain:
        if not isinstance(name, str):
            raise ConfigurationError(
                f"The {display_name} {unit} names must be strings; got {describe_value(name)}.",
            )
    known = {field.name for field in fields(policy_cls)}
    unknown = sorted(name for name in plain if name not in known)
    if unknown:
        raise ConfigurationError(
            f"Unknown {display_name.replace(' ', '-')} {unit}(s): {', '.join(unknown)}. "
            f"Valid {unit}s: {', '.join(sorted(known))}.",
        )
    return policy_cls(**plain)
