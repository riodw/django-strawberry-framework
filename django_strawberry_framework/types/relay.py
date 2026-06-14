"""Internal Relay helpers - interface injection, node resolver defaults, and GlobalID strategies.

Slice 2 introduced ``install_is_type_of``; Slice 4 extends this module with
the interface base-class injection step and the four Relay node resolver
defaults. The helpers split by lifecycle phase:

- Class-creation time (``__init_subclass__``): ``install_is_type_of``
  (Slice 2). Discriminator: ``cls.__dict__`` membership.
- Annotation synthesis time (``_build_annotations``): the
  ``relay.Node in interfaces`` tuple-membership check (Slice 3, in
  ``types/base.py``).
- Finalization Phase 2.5 (``finalize_django_types()``): ``apply_interfaces``,
  ``_check_composite_pk_for_relay_node``, ``install_relay_node_resolvers``
  (Slice 4). The last uses the ``__func__`` identity test that distinguishes
  consumer-overridden ``resolve_*`` methods from the ``relay.Node`` defaults
  inherited through MRO.

Direct ports of behavior from ``strawberry_django/type.py`` and
``strawberry_django/relay/utils.py`` cited in the spec; the upstream
package is not imported at runtime.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.db import models
from django.db.models import CompositePrimaryKey
from strawberry import relay
from strawberry.relay.exceptions import NodeIDAnnotationError
from strawberry.utils.inspect import in_async_context

from ..exceptions import ConfigurationError

# ``SyncMisuseError`` moved to ``utils/querysets.py`` in the 0.0.9 DRY pass
# (``docs/feedback.md`` Major 1); the redundant ``as`` alias re-exports it from
# this module so ``from ...types.relay import SyncMisuseError`` and the
# ``types/__init__.py`` re-export keep working unchanged.
from ..utils.querysets import SyncMisuseError as SyncMisuseError
from ..utils.querysets import (
    apply_type_visibility_async,
    apply_type_visibility_sync,
    initial_queryset,
)

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import (Slice 4 quoted hint).
    from .definition import DjangoTypeDefinition


def implements_relay_node(type_cls: type) -> bool:
    """Return whether ``type_cls`` is a subclass of ``strawberry.relay.Node``.

    Used by ``finalize_django_types()`` Phase 2.5 (after ``__bases__``
    mutation) to decide whether to run the composite-pk gate and the
    four ``resolve_*`` defaults. Distinct from Slice 3's tuple-membership
    check (``relay.Node in interfaces`` at ``types/base.py``), which
    runs pre-base-injection at collection time against the validated
    ``Meta.interfaces`` tuple.
    """
    return issubclass(type_cls, relay.Node)


# Attribute the root ``node``/``nodes`` resolvers (the root ``relay.py``'s
# ``_stamp_node_type``) set on a fetched model instance to carry the
# decode-resolved ``DjangoType`` into abstract-type resolution. Without it, a
# model with TWO registered Relay types makes every candidate's installed
# ``is_type_of`` answer ``True`` for the same bare instance and graphql-core's
# candidate-iteration order picks the ``__typename`` - regardless of which
# type the GlobalID named (Round-4 review S2). The hint is the missing wire
# between the decode routing (which type's resolvers fetched the row) and
# graphql-core's concrete-type selection.
_NODE_TYPE_HINT_ATTR = "_dsf_node_type_hint"


def install_is_type_of(type_cls: type) -> None:
    """Borrow strawberry-django's ``is_type_of`` virtual-subclass behavior.

    Direct port of ``strawberry_django/type.py::_process_type``
    (the ``if "is_type_of" not in cls.__dict__`` branch). Strawberry's
    interface dispatch uses ``is_type_of`` to identify the concrete type
    for a returned ORM instance. Without this borrow, an interface field
    that returns a Django model can fail Strawberry's isinstance check
    and surface as "Cannot determine type for object of model X" at
    runtime (spec-015 Decision 6 #"injection (Decision-1 borrow) is added unconditionally").

    A ``_NODE_TYPE_HINT_ATTR`` stamp (set by the root refetch fields on the
    instances they fetch) takes precedence over the isinstance fallback: the
    hint names the exact ``DjangoType`` whose resolvers fetched the row, so a
    multi-type model resolves ``__typename`` to the type the GlobalID named
    instead of whichever candidate graphql-core happens to test first.
    Unstamped instances (relation resolvers, consumer resolvers) keep the
    pre-032 isinstance behavior unchanged.

    Preserves a consumer-declared ``is_type_of`` via the ``cls.__dict__``
    membership check (the same discriminator strawberry-django uses); a
    function inherited from a base does not count as "declared on this
    class" and is overwritten by the framework default.

    The upstream ``get_strawberry_type_cast`` branch is intentionally
    omitted - our package does not yet expose ``strawberry.cast(...)``
    integration anywhere else, and adding it now would couple this slice
    to a Strawberry surface we have not committed to. If a future adopter
    needs ``strawberry.cast(...)`` support, a focused follow-up slice can
    add the branch without churn to the rest of the Relay machinery.
    """
    if "is_type_of" in type_cls.__dict__:
        return
    model = _model_for(type_cls)

    def is_type_of(obj: object, info: object) -> bool:  # noqa: ARG001
        hinted = getattr(obj, _NODE_TYPE_HINT_ATTR, None)
        if hinted is not None:
            return hinted is type_cls
        return isinstance(obj, (type_cls, model))

    type_cls.is_type_of = is_type_of


def apply_interfaces(type_cls: type, definition: DjangoTypeDefinition) -> None:
    """Inject ``definition.interfaces`` into ``type_cls.__bases__`` (Phase 2.5).

    Skips interfaces already in ``type_cls.__mro__`` so a class that
    already inherits a listed interface directly (e.g. consumer wrote
    ``class Foo(DjangoType, relay.Node): class Meta: interfaces =
    (relay.Node,)``) sees no double-injection
    (spec-015 #"A class that already inherits from one of the listed",
    spec-015 #"only those not already present in",
    spec-015 #"Inherited interfaces via parent").

    Raises:
        ConfigurationError: a ``TypeError`` from ``cls.__bases__``
            assignment is wrapped with the offending interface named in
            the message so consumers see "cannot add interface X" rather
            than a raw layout TypeError
            (spec-015 Risk note #"surface any `TypeError` as a `ConfigurationError`").
    """
    additions = tuple(iface for iface in definition.interfaces if iface not in type_cls.__mro__)
    if not additions:
        return
    try:
        type_cls.__bases__ = (*type_cls.__bases__, *additions)
    except TypeError as exc:
        offending = ", ".join(iface.__name__ for iface in additions)
        raise ConfigurationError(
            f"{type_cls.__name__}: cannot add interface(s) {offending} to bases. "
            f"Python rejected the resulting MRO ({exc}). Either drop the "
            "incompatible interface from Meta.interfaces or rework the class "
            "hierarchy.",
        ) from exc


def _check_composite_pk_for_relay_node(type_cls: type) -> None:
    """Raise ``ConfigurationError`` when a Relay-declared type has a composite pk.

    Decision 2 (spec-015 #"Composite primary keys (Django 5.2+) are explicitly out of scope"):
    combining ``relay.Node`` with a composite-primary-key model is explicitly out of scope for
    ``0.0.5``. Detection uses ``isinstance(model._meta.pk,
    CompositePrimaryKey)`` so the gate aligns with Django 5.2+'s
    native composite-pk type.

    The error message proposes "declare an explicit ``id: relay.NodeID[...]``
    annotation" as a remediation; honor that here so a consumer who
    escapes the composite-pk surface with a single-column ``NodeID``
    annotation is not unconditionally rejected. Strawberry's
    ``Node.resolve_id_attr()`` returns the consumer's ``NodeID``
    attribute name when present and raises ``NodeIDAnnotationError``
    otherwise; only the latter case is the contract violation this
    gate is meant to catch.
    """
    model = _model_for(type_cls)
    if not isinstance(model._meta.pk, CompositePrimaryKey):
        return
    # Ask Strawberry's annotation scan directly rather than
    # ``type_cls.resolve_id_attr()``: a relay-shaped child of a relay-shaped
    # parent inherits the parent's installed framework default, which
    # swallows ``NodeIDAnnotationError`` into the ``"pk"`` fallback and
    # would let a composite-pk child slip past this gate.
    try:
        relay.Node.resolve_id_attr.__func__(type_cls)  # type: ignore[attr-defined]
    except NodeIDAnnotationError:
        pass
    else:
        return
    raise ConfigurationError(
        f"{model.__name__}: relay.Node is not supported on models with a "
        "composite primary key. Either declare an explicit id: "
        "relay.NodeID[...] annotation on the DjangoType or remove "
        "relay.Node from Meta.interfaces.",
    )


# Framework slot ``_stamp_relay_id_attr`` pins each finalized Relay type's
# resolved id attribute into (read via ``cls.__dict__`` so a subclass NEVER
# inherits its parent's stamp). Deliberately NOT Strawberry's ``_id_attr``
# slot: stamping ``"pk"`` there would satisfy upstream's inherited-cache
# check on a chain child and silently bypass the composite-pk gate's
# ``NodeIDAnnotationError`` detection - the exact bug class the Round-4 S1
# gate hardening removed.
_RELAY_ID_ATTR_SLOT = "_dsf_relay_id_attr"


def _stamp_relay_id_attr(type_cls: type) -> None:
    """Resolve the Relay id attribute ONCE and pin it on the class (Phase 2.5).

    Two defects in the per-call path this replaces (Round-4 follow-up):

    - **Order-dependent shadowing.** Strawberry's ``Node.resolve_id_attr``
      caches its scan result on ``cls._id_attr``, and its cache check reads
      INHERITED values - so in a chain where parent and child declare
      DIFFERENT ``relay.NodeID[...]`` annotations, whichever class resolved
      first decided the child's id attribute (the child silently emitted and
      filtered on the parent's column). Seeding ``_id_attr = None`` into the
      class's OWN ``__dict__`` blinds the inherited-cache read, so the scan
      below always starts from this class's annotations.
    - **Per-row rescan.** Upstream caches only on success; the common
      no-``NodeID`` ``"pk"`` fallback re-ran the full MRO ``eval_type``
      annotation scan on EVERY ``resolve_id`` call - once per row of every
      result set. The stamp turns that into one ``__dict__`` read.

    The seed-then-scan keeps upstream as the single scan implementation (no
    ported annotation walk to drift). Stamped unconditionally for every
    Relay-Node-shaped type: when the consumer overrode ``resolve_id_attr``
    the stamp is simply never read (the framework default is not installed).
    Idempotent across partial-finalize reruns.
    """
    type_cls._id_attr = None
    try:
        id_attr = relay.Node.resolve_id_attr.__func__(type_cls)  # type: ignore[attr-defined]
    except NodeIDAnnotationError:
        id_attr = "pk"
    setattr(type_cls, _RELAY_ID_ATTR_SLOT, id_attr)


def _resolve_id_attr_default(cls: type) -> str:
    """Default ``Node.resolve_id_attr`` - stamped at finalize, ``"pk"`` fallback.

    Reads the ``_stamp_relay_id_attr`` slot from the class's OWN
    ``__dict__`` first - every registered Relay type is stamped at
    Phase 2.5, so this is the steady-state path: one dict read per call,
    deterministic at any inheritance depth (each chain class carries its
    own stamp; nothing is inherited).

    The live-scan fallback serves unstamped callers only (a subclass
    defined AFTER finalization, or direct unit calls): it asks
    ``relay.Node.resolve_id_attr`` directly (via ``__func__`` so it binds
    the runtime ``cls``) and maps ``NodeIDAnnotationError`` to ``"pk"`` -
    the ported ``strawberry_django/relay/utils.py::resolve_model_id_attr``
    semantics.

    Deliberately NOT ``super(cls, cls).resolve_id_attr()``: with ``cls``
    bound at runtime, a relay-shaped DjangoType subclassing another
    relay-shaped DjangoType inherits the parent's installed copy of this
    default, and the MRO walk from the child lands back on that copy
    re-bound to the child - infinite recursion (Round-4 review S1). The
    direct call asks Strawberry's annotation scan the same question
    without traversing the MRO's method chain, so the default behaves
    identically at every inheritance depth. (Skipping installation on
    the child is then harmless: all four defaults are stateless
    classmethods that act on the runtime ``cls``.)
    """
    stamped = cls.__dict__.get(_RELAY_ID_ATTR_SLOT)
    if stamped is not None:
        return stamped
    try:
        return relay.Node.resolve_id_attr.__func__(cls)  # type: ignore[attr-defined]
    except NodeIDAnnotationError:
        return "pk"


def _resolve_id_default(cls: type, root: models.Model, *, info: Any) -> str:  # noqa: ARG001
    """Default ``Node.resolve_id`` with a ``__dict__`` cache check.

    Signature mirrors ``strawberry.relay.Node.resolve_id`` after
    ``classmethod`` binding: ``(cls, root, *, info)``. ``info`` is
    keyword-only so Strawberry's Relay machinery, which calls
    ``cls.resolve_id(root, info=info)``, lands at the right slot without
    a positional collision.

    Calls ``cls.resolve_id_attr()`` to derive the column name (handles
    consumer ``relay.NodeID[...]`` overrides and the ``"pk"`` fallback),
    coerces the literal ``"pk"`` to the model's concrete pk ``attname``
    so the dict-cache lookup keys on the real column, then reads from
    ``root.__dict__`` first (avoids an extra ORM hit when the optimizer
    already loaded the row) and falls back to ``getattr(root, id_attr)``
    (spec-015 #"id_attr = cls.resolve_id_attr" / Decision 7's "no
    avoidable lazy loads on ``resolve_id``").

    Keying on ``root.__class__._meta.pk.attname`` is deliberate: the
    alternative ``cls.__django_strawberry_definition__.model._meta.pk.attname``
    would mis-key the ``__dict__`` lookup for proxy-model rows whose actual
    class differs from the declared DjangoType model.
    """
    id_attr = cls.resolve_id_attr()
    if id_attr == "pk":
        id_attr = root.__class__._meta.pk.attname
    try:
        return str(root.__dict__[id_attr])
    except KeyError:
        return str(getattr(root, id_attr))


def _coerce_node_id(node_id: Any) -> Any:
    return node_id.node_id if isinstance(node_id, relay.GlobalID) else node_id


def _coerce_node_ids(node_ids: Any) -> list[Any] | None:
    if node_ids is None:
        return None
    return [_coerce_node_id(node_id) for node_id in node_ids]


def _apply_node_filter(
    qs: models.QuerySet,
    id_attr: str,
    *,
    node_id: Any = None,
    node_ids: list[Any] | None = None,
) -> models.QuerySet:
    """Apply the Relay-id filter to ``qs`` (color-agnostic).

    The lazy ``.filter`` call is identical on sync and async paths; the
    terminal materialization is what differs (``.get``/``.first`` on the
    sync path, ``.aget``/``.afirst`` on the async path).
    """
    if node_id is not None:
        coerced = _coerce_node_id(node_id)
        return qs.filter(**{id_attr: coerced})
    if node_ids is not None:
        return qs.filter(**{f"{id_attr}__in": node_ids})
    return qs


def _model_for(cls: type) -> type[models.Model]:
    """Return the registered model for ``cls.__django_strawberry_definition__``.

    Centralizes the ``cls.__django_strawberry_definition__.model`` lookup
    so model-only reads share one source of truth with the queryset-variant
    lookup in ``utils/querysets.py::initial_queryset``. Mirrors that helper's
    contract: callers are responsible for ``cls`` being a registered
    ``DjangoType``; a missing definition surfaces as a raw ``AttributeError``.
    """
    return cls.__django_strawberry_definition__.model


# Keep the GlobalID strategy helpers in this Relay foundation module; do not
# create a parallel public module for 0.0.9 (spec-031 Decision 11). The public
# testing helpers belong to the sibling Full Relay card.


def _resolve_globalid_strategy(
    definition: DjangoTypeDefinition,
) -> str | Callable[..., str]:
    """Resolve a type's effective raw GlobalID strategy by the three-tier precedence.

    Precedence (spec-031 Decision 5): the per-type ``Meta.globalid_strategy``
    override (already validated at type creation) -> the schema-wide
    ``RELAY_GLOBALID_STRATEGY`` setting (read defensively as "absent -> package
    default") -> the ``DEFAULT_GLOBALID_STRATEGY`` (``"model"``) package default.

    The setting branch is validated through the SAME ``_validate_globalid_strategy``
    rule the ``Meta`` path uses (one validator, two sources - spec-031 Decisions
    6/7), so an unknown string, a wrong-arity callable, or an ``async def``
    callable in ``RELAY_GLOBALID_STRATEGY`` raises ``ConfigurationError`` naming
    the setting rather than failing opaquely from the installed closure.
    ``conf.py`` is a thin reader that does not validate domain values, so the
    validation belongs here.

    Returns the resolved raw strategy (a string in ``STRING_GLOBALID_STRATEGIES``
    or a validated callable); never ``None``.

    Called at finalization (Slice 2's ``install_globalid_typename_resolver``)
    for a type the Relay-shape gate already accepted, so the setting-path
    validation passes ``relay_shaped=True`` (its per-type gate does not re-run).
    """
    # In-function imports: ``base.py`` imports ``install_is_type_of`` from this
    # module at module top, so a module-top ``relay.py -> base.py`` import would
    # close the load cycle. This resolver is only called at finalization - well
    # after module load - so the local import resolves cheaply. Same cycle-dodge
    # justification ``base.py`` documents for its ``FilterSet`` / ``OrderSet``
    # in-function imports. Do NOT hoist either import to module top.
    from ..conf import settings as conf_settings
    from .base import (
        DEFAULT_GLOBALID_STRATEGY,
        _validate_globalid_strategy,
    )

    strategy = definition.globalid_strategy
    if strategy is not None:
        return strategy
    setting = getattr(conf_settings, "RELAY_GLOBALID_STRATEGY", None)
    if setting is not None:
        return _validate_globalid_strategy(
            None,
            setting,
            relay_shaped=True,
            source="setting",
        )
    return DEFAULT_GLOBALID_STRATEGY


# Single source of truth for the "strategy -> payload shape" mapping (spec-031
# Slice 2/3 plan, DRY watch point). The string constants ``STRING_GLOBALID_STRATEGIES``
# / ``DEFAULT_GLOBALID_STRATEGY`` live in ``types/base.py`` (Slice 1); these are the
# payload-shape memberships the encoder, the model-label-routing audit, the
# strategy-aware filter (``filters/base.py``), and the Slice-3 decoder all
# reference rather than re-typing ``{"model", "type+model"}`` / ``{"type",
# "type+model"}`` at each site. ``callable`` and ``custom`` are intentionally in
# neither set: they are encode-only in 0.0.9 (no decode path), so the decoder's
# "no decode for these" contract IS their absence from both memberships - there
# is deliberately no ``{"callable", "custom"}`` literal.
MODEL_LABEL_STRATEGIES = frozenset({"model", "type+model"})
TYPE_NAME_STRATEGIES = frozenset({"type", "type+model"})


def _emits_model_label(effective_strategy: str | None) -> bool:
    """Return whether a recorded effective strategy emits the model-label slot.

    ``model`` and ``type+model`` both emit ``app_label.modelname`` in the
    ``GlobalID`` type-name slot. Used by the encoder closure (which slot to
    emit) and the model-label-routing audit (the ``emits_model_label`` half).
    """
    return effective_strategy in MODEL_LABEL_STRATEGIES


def _accepts_model_label_decode(effective_strategy: str | None) -> bool:
    """Return whether a recorded effective strategy can decode a model-label slot.

    Identical membership to ``_emits_model_label`` - ``model`` and ``type+model``
    both decode model labels - but named distinctly because the audit's
    ``accepts_model_label(primary)`` predicate and the Slice-3 decode-Step-2
    enforcement read the *acceptance* side. Encode and decode acceptance of the
    model-label shape coincide for the framework strategies, so one frozenset
    serves both; Slice 3 splits this if a divergence ever surfaces.
    """
    return effective_strategy in MODEL_LABEL_STRATEGIES


def _accepts_type_name_decode(effective_strategy: str | None) -> bool:
    """Return whether a recorded effective strategy can decode a GraphQL-type-name slot.

    ``type`` and ``type+model`` both accept a bare ``graphql_type_name`` payload.
    Sibling of ``_accepts_model_label_decode`` for the type-name shape. Read by
    BOTH the Slice-3 decode-Step-2 enforcement (the no-dot branch) AND
    ``filters/base.py::_accepted_globalid_type_names`` (the strategy-aware filter),
    so the ``{"type", "type+model"}`` membership lives in one place
    (``TYPE_NAME_STRATEGIES``) instead of being re-typed at each site.
    """
    return effective_strategy in TYPE_NAME_STRATEGIES


def encode_typename(
    definition: DjangoTypeDefinition,
    strategy: str | Callable[..., str],
    type_cls: type,
    root: Any,
    info: Any,
) -> str:
    """Compute the ``GlobalID`` type-name slot for one resolved strategy.

    The single per-strategy slot computation (spec-031 Decision 4), invoked by
    the installed ``resolve_typename`` closure:

    - ``model`` / ``type+model`` -> ``definition.model._meta.label_lower``
      (Django's canonical ``"app_label.modelname"``, e.g. ``products.item``).
    - ``type`` -> ``definition.graphql_type_name`` (matches Strawberry's
      ``info.path.typename`` default; the framework installs a ``type`` closure
      only when shadowing a framework closure inherited from a concrete Relay
      parent - see ``install_globalid_typename_resolver`` step 2 - so this
      branch is the live implementation for exactly that shape).
    - callable -> the consumer callable's ``(type_cls, model, root, info) -> str``
      return, validated non-empty ``str``. A non-``str`` or empty return raises
      ``ConfigurationError`` naming the type and the contract, rather than
      letting Strawberry's ``Node._id`` ``assert isinstance(type_name, str)``
      fire as an opaque ``AssertionError`` (spec-031 Decision 4/10).
      The callable's arity / sync-ness were already
      validated at type creation (Slice 1) - this is ONLY the per-call
      return-value check.
    """
    if callable(strategy):
        result = strategy(type_cls, definition.model, root, info)
        if not isinstance(result, str) or not result:
            raise ConfigurationError(
                f"{definition.graphql_type_name}: the Meta.globalid_strategy callable "
                f"returned {result!r}; a (type_cls, model, root, info) -> str encoder "
                "must return a non-empty string for the GlobalID type-name slot.",
            )
        return result
    if strategy in MODEL_LABEL_STRATEGIES:
        return definition.model._meta.label_lower
    # ``type`` (the only remaining string strategy): the GraphQL type name.
    return definition.graphql_type_name


# Sentinel attribute stamped on every framework-installed ``resolve_typename``
# closure (``_install_typename_closure``). The override test below keys on it
# so a framework closure inherited from a CONCRETE Relay parent through the MRO
# is never mistaken for a consumer override - without the marker, a concrete
# Relay child of a concrete Relay parent would see the parent's installed
# closure fail the ``__func__`` identity test and be misclassified ``custom``
# (silently encode-only, audit-blind, and spuriously both-declared when the
# child carries its own ``Meta.globalid_strategy``). The attribute lives on the
# plain function so it survives ``classmethod.__func__`` retrieval.
_FRAMEWORK_CLOSURE_MARKER = "_dsf_globalid_framework_closure"


def _inherits_framework_closure(type_cls: type) -> bool:
    """Return whether ``type_cls``'s MRO-resolved ``resolve_typename`` is a framework closure.

    True when the attribute (own or inherited) is a closure
    ``_install_typename_closure`` stamped with ``_FRAMEWORK_CLOSURE_MARKER``.
    Read by ``install_globalid_typename_resolver`` to decide whether a
    ``type``-classified type must install its OWN closure: inheriting a
    parent's framework closure would otherwise shadow Strawberry's default and
    emit the PARENT's payload (the parent ``definition`` is captured in the
    inherited closure).
    """
    existing_func = getattr(getattr(type_cls, "resolve_typename", None), "__func__", None)
    return getattr(existing_func, _FRAMEWORK_CLOSURE_MARKER, False)


def _consumer_overrode_resolve_typename(type_cls: type) -> bool:
    """Return whether ``type_cls`` declares its own ``resolve_typename``.

    MRO-aware ``existing.__func__ is relay.Node.resolve_typename.__func__``
    identity test - the same discriminator ``install_relay_node_resolvers``
    uses for the four ``resolve_*`` defaults. ``resolve_typename`` is a
    ``@classmethod`` on ``relay.Node`` so it carries ``__func__`` exactly like
    those. A method inherited unchanged from ``relay.Node`` (or absent) is NOT
    an override - and neither is a framework closure installed on a concrete
    Relay PARENT and inherited through the MRO (discriminated by
    ``_FRAMEWORK_CLOSURE_MARKER``; the step-0 re-entrancy guard protects the
    same definition across finalize re-runs, but only the marker protects a
    DIFFERENT definition inheriting the installed closure). A consumer override
    inherited from an abstract base lacks the marker, so it still classifies
    ``custom`` - the intended semantics. Only a consumer-declared method is an
    override.
    """
    existing = getattr(type_cls, "resolve_typename", None)
    existing_func = getattr(existing, "__func__", None)
    if existing is None or existing_func is None:
        return False
    if getattr(existing_func, _FRAMEWORK_CLOSURE_MARKER, False):
        return False
    node_func = getattr(relay.Node.resolve_typename, "__func__", None)
    return existing_func is not node_func


def install_globalid_typename_resolver(type_cls: type, definition: DjangoTypeDefinition) -> None:
    """Inject the strategy-parameterized ``resolve_typename`` default (Phase 2.5).

    Runs alongside ``install_relay_node_resolvers`` for every Relay-Node-shaped
    type, in the ordered steps of spec-031 Decision 10:

    0. **Re-entrancy guard.** If ``definition.effective_globalid_strategy`` is
       already set, this type was processed in a prior (possibly partial)
       finalize run - skip override-detection, recording, and install, leaving
       the recorded classification and any installed closure intact
       (spec-031 Decision 10). Load-bearing: a Phase-2.5 raise (including the
       model-label-routing audit) leaves every type ``finalized = False``, so a
       re-run re-enters the finalizer loop; without this guard the ``__func__``
       test would re-run against the *now-installed framework closure* and
       misclassify the type ``custom``.
    1. **Override detection.** If the consumer overrode ``resolve_typename``:
       declaring an explicit ``Meta.globalid_strategy`` too is a both-declared
       conflict -> ``ConfigurationError`` (the schema-wide
       ``RELAY_GLOBALID_STRATEGY`` setting is NOT a conflict - only the per-type
       ``Meta`` key collides); otherwise the effective strategy is ``custom``,
       install nothing (the override owns the slot).
    2. **No override.** Resolve the raw strategy via
       ``_resolve_globalid_strategy``; install the framework closure for
       ``model`` / ``type+model`` / ``callable`` (the closure validates a
       non-empty ``str`` callable return); install NOTHING for ``type``
       (Strawberry's default returns ``info.path.typename``, byte-identical to
       pre-0.0.9) - UNLESS the MRO-resolved attribute is a framework closure
       inherited from a concrete Relay parent, in which case ``type`` installs
       its own closure too (``encode_typename``'s ``type`` branch): the
       inherited closure captured the PARENT's definition and would otherwise
       keep shadowing Strawberry's default, emitting the parent's payload.
    3. **Record** the classification string (``model`` / ``type`` /
       ``type+model`` / ``callable`` / ``custom``) on
       ``definition.effective_globalid_strategy`` - the single value decode and
       the strategy-aware filter read, and the step-0 sentinel.
    """
    if definition.effective_globalid_strategy is not None:
        return

    if _consumer_overrode_resolve_typename(type_cls):
        if definition.globalid_strategy is not None:
            raise ConfigurationError(
                f"{definition.graphql_type_name}: declares both a resolve_typename "
                "override and an explicit Meta.globalid_strategy. These are two "
                "contradictory sources for the GlobalID type-name slot; declare a "
                "resolve_typename override OR Meta.globalid_strategy, not both.",
            )
        definition.effective_globalid_strategy = "custom"
        return

    strategy = _resolve_globalid_strategy(definition)
    classification = "callable" if callable(strategy) else strategy

    if classification != "type" or _inherits_framework_closure(type_cls):
        _install_typename_closure(type_cls, definition, strategy)
    definition.effective_globalid_strategy = classification


def _install_typename_closure(
    type_cls: type,
    definition: DjangoTypeDefinition,
    strategy: str | Callable[..., str],
) -> None:
    """Install the framework ``resolve_typename`` classmethod capturing ``strategy``.

    The closure mirrors Strawberry's ``resolve_typename(root, info)`` seam and is
    installed via ``setattr(type_cls, "resolve_typename", classmethod(...))``.
    The strategy is resolved once here (at finalization), not per request, so the
    ``id``-resolution hot path does no strategy lookup (spec-031 Decision 5).
    ``model`` / ``type+model`` / ``callable`` always reach here; ``type``
    reaches here only when shadowing a framework closure inherited from a
    concrete Relay parent (otherwise ``type`` keeps Strawberry's default). The
    closure is stamped with ``_FRAMEWORK_CLOSURE_MARKER`` so the override test
    never mistakes it - inherited through a subclass's MRO - for a consumer
    override.
    """

    def resolve_typename(cls: type, root: Any, info: Any) -> str:
        return encode_typename(definition, strategy, cls, root, info)

    setattr(resolve_typename, _FRAMEWORK_CLOSURE_MARKER, True)
    type_cls.resolve_typename = classmethod(resolve_typename)


def decode_global_id(gid: relay.GlobalID | str) -> tuple[type, str]:
    """Decode a ``GlobalID`` to its ``(DjangoType, node_id)`` via resolve-then-enforce.

    The decode half of the GlobalID-encoding feature (spec-031 Decision 8). It is
    the forward-looking piece root ``node(id:)`` / ``nodes(ids:)``
    (``WIP-ALPHA-032-0.0.9``) will consume - no shipped ``0.0.9`` path calls it
    yet - so it is validated directly by package tests.

    Because its eventual caller feeds it arbitrary client-controlled input, every
    failure mode surfaces ONE uniform ``ConfigurationError`` (the
    ``RelatedFilter``-style fail-loud message naming the resolution attempt)
    rather than leaking Strawberry's ``GlobalIDValueError`` or Python's
    ``KeyError`` / ``AttributeError`` / ``TypeError``.

    Steps:

    - **Input gate.** A value outside ``(relay.GlobalID, str)`` (``None``, an
      ``int``, a lazy object) is rejected up front, before any parse.
    - **Parse.** A ``relay.GlobalID`` is read directly; a ``str`` is parsed via
      ``relay.GlobalID.from_id`` (catching the ``ValueError`` superset that covers
      ``GlobalIDValueError``). An empty ``type_name`` or empty ``node_id`` is
      rejected (``from_id`` does not enforce non-empty slots; the encoder never
      emits an empty type-name slot and the package has no blank-string pks).
    - **Step 1 - resolve a candidate.** A model-label slot (the ``type_name``
      contains a dot, ``"app_label.modelname"``) resolves via
      ``apps.get_model`` -> ``registry.get(model)`` (the primary / lone type,
      honoring ``Meta.primary``). A GraphQL-type-name slot (no dot) resolves via
      ``registry.definition_for_graphql_name`` (keyed on ``graphql_type_name``,
      Relay-Node definitions only).
    - **Step 2 - enforce the recorded strategy permits the payload shape.** Reads
      the candidate's stamped ``effective_globalid_strategy``: a model-label
      payload is permitted iff ``_accepts_model_label_decode`` (``model`` /
      ``type+model``); a type-name payload iff ``_accepts_type_name_decode``
      (``type`` / ``type+model``). ``callable`` / ``custom`` are in neither
      membership (encode-only in ``0.0.9``), and an absent (``None``) strategy
      (a non-Relay-Node ``DjangoType`` or a mid-state type) is rejected - so a
      crafted ID cannot resolve to a type that cannot be a Node.

    Returns ``(target_type, node_id)`` where ``target_type`` is the resolved
    ``DjangoType`` class (``definition.origin``) and ``node_id`` is the parsed id
    string.
    """
    # ``registry`` is reached in-function: ``registry.py`` imports
    # ``implements_relay_node`` from this module in-function, and ``relay.py``
    # must not import ``registry`` at module top - the same cycle-dodge
    # ``_resolve_globalid_strategy`` above documents for its ``conf`` / ``base``
    # imports. Decode runs well after module load, so the local import is cheap.
    from ..registry import registry

    if not isinstance(gid, (relay.GlobalID, str)):
        raise ConfigurationError(
            f"decode_global_id: expected a relay.GlobalID or its base64 string, got "
            f"{type(gid).__name__}. A GlobalID must be the encoded id, not a raw payload.",
        )

    if isinstance(gid, str):
        try:
            decoded = relay.GlobalID.from_id(gid)
        except ValueError as exc:
            raise ConfigurationError(
                f"decode_global_id: {gid!r} is not a valid GlobalID (malformed base64 or "
                "not a 'type_name:node_id' shape).",
            ) from exc
    else:
        decoded = gid

    type_name = decoded.type_name
    node_id = decoded.node_id
    if not type_name or not node_id:
        raise ConfigurationError(
            f"decode_global_id: GlobalID has an empty slot (type_name={type_name!r}, "
            f"node_id={node_id!r}); both must be non-empty.",
        )

    is_model_label = "." in type_name
    if is_model_label:
        app_label, model_name = type_name.split(".", 1)
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError as exc:
            raise ConfigurationError(
                f"decode_global_id: model label {type_name!r} resolves to no installed "
                "Django model.",
            ) from exc
        target_type = registry.get(model)
        if target_type is None:
            raise ConfigurationError(
                f"decode_global_id: model {type_name!r} has no registered (primary) "
                "Relay-Node DjangoType to decode to.",
            )
        definition = registry.get_definition(target_type)
    else:
        definition = registry.definition_for_graphql_name(type_name)
        target_type = definition.origin

    strategy = definition.effective_globalid_strategy if definition is not None else None
    if strategy is None:
        raise ConfigurationError(
            f"decode_global_id: {type_name!r} resolves to a type with no recorded GlobalID "
            "strategy; it is not a framework-decodable Relay-Node DjangoType.",
        )
    permitted = (
        _accepts_model_label_decode(strategy)
        if is_model_label
        else _accepts_type_name_decode(strategy)
    )
    if not permitted:
        raise ConfigurationError(
            f"decode_global_id: {type_name!r} ({'model-label' if is_model_label else 'type-name'} "
            f"payload) is not decodable under the candidate's {strategy!r} strategy "
            "(callable / custom strategies are encode-only in 0.0.9).",
        )

    return target_type, node_id


def _order_nodes(
    cls: type,
    results: list,
    coerced_keys: list[str],
    id_attr: str,
    *,
    required: bool,
) -> list:
    """Re-order ``results`` to match ``coerced_keys`` (port of strawberry-django's map_results).

    Mirrors ``strawberry_django/relay/utils.py::resolve_model_nodes #"def map_results"``: build an index
    keyed on ``str(getattr(obj, id_attr))`` (so the dict lookup matches
    the ``coerced_keys`` shape - both are ``str``) and emit one entry per
    requested key.

    ``required=True`` raises the model's ``DoesNotExist`` for any missing
    key - homogeneous with ``_resolve_node_default``'s ``qs.get()`` so
    consumers writing visibility-aware exception handling can catch a
    single exception type for the "required missing id" semantic.
    ``required=False`` emits ``None`` for missing keys.
    """
    index = {str(getattr(obj, id_attr)): obj for obj in results}
    output: list = []
    model = _model_for(cls)
    for key in coerced_keys:
        if required:
            try:
                output.append(index[key])
            except KeyError as exc:
                raise model.DoesNotExist(
                    f"{model.__name__}: no row matching {id_attr}={key!r}.",
                ) from exc
        else:
            output.append(index.get(key))
    return output


def _resolve_node_default(
    cls: type,
    node_id: Any,
    *,
    info: Any,
    required: bool = False,
) -> Any:
    """Default ``Node.resolve_node`` - ``get_queryset`` aware.

    Signature mirrors ``strawberry.relay.Node.resolve_node`` after
    ``classmethod`` binding: ``(cls, node_id, *, info, required=False)``.
    ``info`` is keyword-only so Strawberry's runtime call shape
    (``cls.resolve_node(node_id, info=info, required=...)``) lands
    correctly. An earlier draft used ``(cls, info, node_id, ...)`` which
    Strawberry's machinery turned into ``TypeError: got multiple values
    for argument 'info'``.

    Returns the single matching row (``qs.get()`` when ``required``,
    ``qs.first()`` otherwise). Async detection uses
    ``strawberry.utils.inspect.in_async_context``; on the async branch
    the returned coroutine awaits ``get_queryset`` (so async
    ``get_queryset`` hooks are honored), applies the id filter, and
    awaits ``aget``/``afirst``. On the sync branch a coroutine returned
    from ``get_queryset`` is rejected with ``SyncMisuseError`` (a
    ``ConfigurationError`` subclass that also inherits ``RuntimeError``)
    rather than silently producing ``AttributeError: 'coroutine'
    object has no attribute 'filter'``.
    """
    id_attr = cls.resolve_id_attr()
    if in_async_context():
        return _resolve_node_async(cls, id_attr, node_id, info=info, required=required)
    qs = apply_type_visibility_sync(cls, initial_queryset(cls), info)
    qs = _apply_node_filter(qs, id_attr, node_id=node_id)
    return qs.get() if required else qs.first()


async def _resolve_node_async(
    cls: type,
    id_attr: str,
    node_id: Any,
    *,
    info: Any,
    required: bool,
) -> Any:
    """Async sibling of ``_resolve_node_default``.

    Awaits the ``get_queryset`` hook (regardless of whether the consumer
    declared it ``def`` or ``async def``) before applying the id filter
    and the final ``aget``/``afirst``. Decision 9 of the spec promises
    both shapes; this is the awaitable that actually delivers on that
    contract.
    """
    qs = await apply_type_visibility_async(cls, initial_queryset(cls), info)
    qs = _apply_node_filter(qs, id_attr, node_id=node_id)
    return await (qs.aget() if required else qs.afirst())


def _resolve_nodes_default(
    cls: type,
    *,
    info: Any,
    node_ids: Any = None,
    required: bool = False,
) -> Any:
    """Default ``Node.resolve_nodes`` - order-preserving, missing-aware.

    Signature mirrors ``strawberry.relay.Node.resolve_nodes`` after
    ``classmethod`` binding: ``(cls, *, info, node_ids, required=False)``.
    ``node_ids`` defaults to ``None`` here (Strawberry's upstream slot is
    a required keyword argument) so the package can offer the bulk-fetch
    "no ids -> full queryset" path documented in the spec without
    forcing callers to thread ``node_ids=None`` explicitly.

    When ``node_ids`` is ``None`` returns the filtered queryset (the
    caller materializes via iteration as needed). When ``node_ids`` is
    provided, returns a list whose indexes correspond 1:1 with
    ``node_ids``: ``required=False`` yields ``None`` for missing ids,
    ``required=True`` raises the model's ``DoesNotExist`` for missing
    ids (homogeneous with ``_resolve_node_default``'s ``qs.get()``).

    Async detection routes through ``in_async_context`` so async
    ``get_queryset`` hooks are awaited before the id filter; in the
    async branch the caller must ``await`` the call to obtain either
    the queryset (``node_ids=None``) or the order-preserving list
    (``node_ids`` provided). Sync resolver contexts cannot await an
    async ``get_queryset`` hook and surface ``SyncMisuseError`` (a
    ``ConfigurationError`` subclass that also inherits ``RuntimeError``)
    instead.
    """
    id_attr = cls.resolve_id_attr()
    if in_async_context():
        return _resolve_nodes_async(cls, id_attr, node_ids, info=info, required=required)
    qs = apply_type_visibility_sync(cls, initial_queryset(cls), info)
    coerced_ids = _coerce_node_ids(node_ids)
    qs = _apply_node_filter(qs, id_attr, node_ids=coerced_ids)
    if coerced_ids is None:
        return qs
    coerced_keys = [str(node_id) for node_id in coerced_ids]
    return _order_nodes(cls, list(qs), coerced_keys, id_attr, required=required)


async def _resolve_nodes_async(
    cls: type,
    id_attr: str,
    node_ids: Any,
    *,
    info: Any,
    required: bool,
) -> Any:
    """Async sibling of ``_resolve_nodes_default``.

    Awaits the ``get_queryset`` hook before applying the id filter so
    async ``get_queryset`` hooks are honored. Returns the queryset
    directly when ``node_ids`` is ``None`` (the caller materializes via
    ``async for``); when ``node_ids`` is provided, materializes via
    ``async for`` and returns the order-preserving list shape.
    """
    qs = await apply_type_visibility_async(cls, initial_queryset(cls), info)
    coerced_ids = _coerce_node_ids(node_ids)
    qs = _apply_node_filter(qs, id_attr, node_ids=coerced_ids)
    if coerced_ids is None:
        return qs
    coerced_keys = [str(node_id) for node_id in coerced_ids]
    results = [obj async for obj in qs]
    return _order_nodes(cls, results, coerced_keys, id_attr, required=required)


# Single source of truth for the four Relay resolver method names plus the
# framework default implementation each one maps to. Iterated by
# ``install_relay_node_resolvers``; appears nowhere else.
_RELAY_RESOLVER_DEFAULTS: tuple[tuple[str, Callable[..., Any]], ...] = (
    ("resolve_id", _resolve_id_default),
    ("resolve_id_attr", _resolve_id_attr_default),
    ("resolve_node", _resolve_node_default),
    ("resolve_nodes", _resolve_nodes_default),
)


def install_relay_node_resolvers(type_cls: type) -> None:
    """Inject the four ``resolve_*`` defaults via the ``__func__`` identity test.

    Step 0 stamps the type's resolved Relay id attribute
    (``_stamp_relay_id_attr``) - the one-time scan whose result the
    installed ``resolve_id_attr`` default reads per call instead of
    re-running Strawberry's annotation walk per row.

    For each ``(name, default)`` pair in ``_RELAY_RESOLVER_DEFAULTS``:

    - Look up the inherited method on ``type_cls`` (resolves through MRO
      to ``relay.Node``'s default if no consumer override exists).
    - Compare ``existing.__func__`` to ``relay.Node.<attr>.__func__``.
      When they match (or ``existing`` is ``None``), the consumer has
      not overridden the method and the framework default is installed
      via ``setattr(type_cls, attr, classmethod(default))``.
    - When they differ, the consumer's override wins and is preserved.

    Direct port of ``strawberry_django/type.py::_process_type``
    (the ``if issubclass(cls, relay.Node)`` branch). The ``__func__``
    discriminator is structurally distinct from Slice 2's ``__dict__``
    membership discriminator (``is_type_of`` injection) and Slice 3's
    tuple-membership discriminator (``relay.Node in interfaces``) - the
    three answer different questions at three lifecycle phases.
    """
    _stamp_relay_id_attr(type_cls)
    for attr, default_impl in _RELAY_RESOLVER_DEFAULTS:
        existing = getattr(type_cls, attr, None)
        node_default = getattr(relay.Node, attr, None)
        existing_func = getattr(existing, "__func__", None)
        node_func = getattr(node_default, "__func__", None)
        if existing is None or (existing_func is not None and existing_func is node_func):
            setattr(type_cls, attr, classmethod(default_impl))
