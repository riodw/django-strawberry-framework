"""Generated-input substrate shared by the filter and order set families.

The filter and order subsystems each build real Strawberry input classes as
module globals (``strawberry.lazy(...)`` resolves through ``module.__dict__``),
keep class-level factory caches, detect duplicate generated input names, and
reset stale binding state during ``registry.clear()``. spec-027 and spec-028
grew those mechanics as parallel copies; this module single-sites the NEUTRAL
machinery so a fix to the materialization ledger, the BFS collision check, or
the namespace-clear lifecycle lands once instead of being hand-mirrored (the
0.0.9 DRY pass, ``docs/feedback.md`` Major 1).

What lives here is mechanics only. Domain semantics stay at the call sites:
``filters/inputs.py`` keeps ``convert_filter_to_input_annotation`` /
``normalize_input_value`` and the operator-bag / logic-field builders;
``orders/inputs.py`` keeps ``convert_order_field_to_input_annotation`` /
``normalize_input_value`` and the ``Ordering`` enum. The two ``inputs`` modules
re-export the helpers below under their spec-named aliases (``FieldSpec`` /
``build_input_class`` / ``_camel_case`` / ``_iter_*set_subclasses``) so existing
imports and the test suite keep addressing them on the family module.

This module depends on neither family package, so both can import it without a
cycle (same contract as ``utils/connections.py``).
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, ClassVar

import strawberry

from ..exceptions import ConfigurationError


@dataclass(frozen=True)
class GeneratedInputFieldSpec:
    """Per-generated-input-field metadata shared across the set families.

    Carries the three names the runtime normalizers need to map between the
    Strawberry input dataclass field, the GraphQL wire-format name, and the
    Django ORM lookup path. Re-exported as ``FieldSpec`` by both
    ``filters/inputs.py`` and ``orders/inputs.py``.
    """

    python_attr: str
    graphql_name: str
    django_source_path: str


# TODO(spec-039 Slice 1): Promote mutation/form/serializer input field specs and
# namespace lifecycle helpers here before adding the serializer input generator.
# Pseudo flow:
#   - Define one frozen `InputFieldSpec` carrying `input_attr`, `graphql_name`,
#     `target_name`, `kind`, and optional `source`.
#   - `make_input_namespace(module_path, family_label)` owns the materialized-name
#     ledger and returns the ledger, a materializer that calls
#     `materialize_generated_input_class(...)`, and a ledger-only clear function.
#   - `make_shape_build_cache()` owns one cache dict and returns it with a clear
#     callback so registry/finalizer cleanup can be registered consistently via
#     static `(module_path, attr)` clear targets.
#
# Existing mutation/form helpers should re-point here so
# `rest_framework/inputs.py` does not become a third ledger/cache copy.
def graphql_camel_name(name: str) -> str:
    """Lowercase the head, then ``PascalCase`` the rest (``galaxy_name`` -> ``galaxyName``).

    Splits on ``_`` and drops empty tokens; returns ``name`` unchanged when it
    has no word tokens (``""`` -> ``""``, ``"_"`` -> ``"_"``).
    """
    parts = [part for part in name.split("_") if part]
    if not parts:
        return name
    head, *rest = parts
    return head + "".join(part.capitalize() for part in rest)


def normalize_field_name_sequence(
    value: Any,
    *,
    label: str = "fields",
    flavor: str,
) -> tuple[str, ...] | None:
    """Return a ``Meta.fields`` / ``Meta.exclude`` value as a tuple of names, or ``None``.

    The flavor-agnostic body shared by ``mutations/sets.py::_normalize_field_sequence``
    and ``forms/inputs.py::normalize_form_field_sequence`` (spec-038 integration
    pass, Finding I1). Both sites normalize a declared field sequence the same way;
    they differed only in the human flavor label interpolated into the two
    ``ConfigurationError`` messages, so that single divergence is hoisted to the
    ``flavor`` parameter -- mirroring how ``mutations/sets.py::make_declaration_registry``
    already parameterizes its reject wording by a flavor label. The
    field-existence-basis check (a name not in the model's editable columns /
    the form's ``base_fields``) stays at each call site; this helper only validates
    the SHAPE of the declared sequence.

    ``None`` means "unset". A non-``None`` value is coerced to a tuple so the bind
    and the generator see one shape. A bare string is rejected (it would iterate
    as characters); a duplicate name is rejected (it would collapse silently when
    the effective field set is taken as a ``frozenset``, masking a malformed
    declaration), failing loud naming the repeated field(s). ``label`` names which
    key (``fields`` / ``exclude``) is at fault; ``flavor`` names the mutation
    base(s) in the message (e.g. ``"DjangoMutation"`` or
    ``"DjangoFormMutation / DjangoModelFormMutation"``).
    """
    if value is None:
        return None
    if isinstance(value, str):
        raise ConfigurationError(
            f"{flavor} Meta.fields / Meta.exclude must be a sequence of field "
            f"names, not a bare string: {value!r}.",
        )
    names = tuple(value)
    seen: set[str] = set()
    duplicates = sorted({name for name in names if name in seen or seen.add(name)})
    if duplicates:
        raise ConfigurationError(
            f"{flavor} Meta.{label} declares duplicate field name(s): "
            f"{duplicates!r}. Each field may appear at most once.",
        )
    return names


def build_strawberry_input_class(
    name: str,
    field_specs: list[tuple[str, Any, dict[str, Any] | None]],
) -> type:
    """Construct a ``@strawberry.input``-decorated dataclass.

    ``field_specs`` is a list of ``(python_attr, annotation, field_kwargs)``
    triples. ``field_kwargs`` may carry ``name=`` for the GraphQL alias,
    ``default=`` for the dataclass default, and ``description=`` for the
    Strawberry field description.

    **A triple that OMITS ``default`` builds a REQUIRED field**: no class
    default is set, so ``@strawberry.input`` renders the field non-null and
    rejects an omitted value at GraphQL coercion. A bare ``None`` default
    (the prior behavior) renders non-null SDL *yet still accepts omission*,
    delivering ``None`` to the resolver and masking the missing-input error
    (``docs/feedback.md`` Finding 2). An OPTIONAL field must therefore pass an
    explicit ``default`` - ``strawberry.UNSET`` for the mutation / form
    ``annotation | None`` widening, ``None`` for the filter / order optional
    inputs (Strawberry tolerates a required field after a defaulted one; its
    inputs are keyword-only).

    The class is constructed via ``type(name, (), namespace)`` rather than
    ``dataclasses.make_dataclass`` because ``make_dataclass`` replaces any
    ``strawberry.field(...)`` default with a plain ``dataclasses.Field`` and
    strips the strawberry-specific metadata (the ``name=`` alias would be
    lost). Setting the ``strawberry.field`` as a class-level attribute
    alongside ``__annotations__`` preserves the metadata through the
    ``@strawberry.input`` decoration.
    """
    namespace: dict[str, Any] = {"__annotations__": {}}
    for python_attr, annotation, raw_kwargs in field_specs:
        kwargs = dict(raw_kwargs or {})
        # The PRESENCE of ``default`` (not its value) decides required-vs-optional:
        # a required field gets NO class default at all, so ``None`` is a legal
        # explicit default for an optional field rather than the required sentinel.
        has_default = "default" in kwargs
        default = kwargs.pop("default", None)
        strawberry_field_kwargs: dict[str, Any] = {}
        if "name" in kwargs:
            strawberry_field_kwargs["name"] = kwargs.pop("name")
        if "description" in kwargs:
            strawberry_field_kwargs["description"] = kwargs.pop("description")
        namespace["__annotations__"][python_attr] = annotation
        if strawberry_field_kwargs:
            # An aliased / described field still needs a ``strawberry.field``;
            # pass ``default`` only when one was supplied so a required aliased
            # field (e.g. a required FK ``categoryId``) stays non-null.
            namespace[python_attr] = (
                strawberry.field(default=default, **strawberry_field_kwargs)
                if has_default
                else strawberry.field(**strawberry_field_kwargs)
            )
        elif has_default:
            namespace[python_attr] = default
        # else: a required, un-aliased field -> NO class attribute, so
        # ``@strawberry.input`` renders it non-null and coercion rejects omission.
    cls = type(name, (), namespace)
    return strawberry.input(cls)


def materialize_generated_input_class(
    name: str,
    cls: type,
    *,
    module_path: str,
    family_label: str,
    ledger: dict[str, type],
) -> None:
    """Pin ``cls`` as a real module global of ``module_path`` under ``name``.

    Strawberry's ``LazyType.resolve_type`` reads
    ``sys.modules[<module>].__dict__[name]`` to materialize an
    ``Annotated[<name>, strawberry.lazy(<module>)]`` reference; this is the
    single entry point that pins ``cls`` at the matching ``__dict__`` slot
    (spec-027 / spec-028 Decision 9).

    Idempotent on the ``(name, cls)`` pair: re-materializing the same class
    under the same name is a no-op (the Decision 9 lifecycle clause -- supports
    partial-finalize recovery without a sentinel pass). A collision against a
    different class under the same ``name`` raises ``ConfigurationError`` naming
    both qualified class names plus the ``family_label`` (``FilterSet`` /
    ``OrderSet``) so the consumer sees the offending pair and family instead of
    a cryptic schema-build error.
    """
    existing = ledger.get(name)
    if existing is cls:
        return
    if existing is not None:
        raise ConfigurationError(
            f"{name!r} is materialized by two distinct {family_label} input classes: "
            f"{existing.__module__}.{existing.__qualname__} vs "
            f"{cls.__module__}.{cls.__qualname__}. Rename one {family_label.lower()} "
            "so its class-derived input type name is unique.",
        )
    module = sys.modules[module_path]
    setattr(module, name, cls)
    ledger[name] = cls


def build_lazy_input_annotation(
    set_class: type,
    *,
    expected_base: type,
    family_name: str,
    expected_label: str,
    ledger: set[type],
    input_type_name_for: Callable[[type], str],
    module_path: str,
) -> object:
    """Return the ``Annotated[..., strawberry.lazy(...)]`` forward-ref for a set's input class.

    The Decision-11 consumer-helper body shared by
    ``filters/__init__.py::filter_input_type`` and
    ``orders/__init__.py::order_input_type`` (the 0.0.9 DRY pass). Validates
    ``set_class`` is an ``expected_base`` subclass -- raising ``TypeError`` with
    the family's wording (``family_name`` + ``expected_label``, e.g.
    ``"filter_input_type() requires a FilterSet subclass; got ..."``) so consumers
    catch misuse at the resolver-declaration site rather than schema-build time --
    records it in the family ``ledger`` (the finalizer's orphan check reads this),
    and builds the canonical Strawberry forward-reference.

    The ForwardRef-wrapped ``Annotated[<runtime str>, strawberry.lazy(<module>)]``
    form is load-bearing: ``LazyType.resolve_type`` resolves it via
    ``module.__dict__`` at schema build, by which point ``finalize_django_types()``
    has materialized the input class as a module global. The type name is passed
    as a runtime-computed string into ``Annotated[...]`` (NOT interpolated into a
    literal outside the call) so the ForwardRef wrapping holds.
    """
    if not (isinstance(set_class, type) and issubclass(set_class, expected_base)):
        raise TypeError(f"{family_name}() requires {expected_label} subclass; got {set_class!r}")
    ledger.add(set_class)
    return Annotated[input_type_name_for(set_class), strawberry.lazy(module_path)]


def iter_set_subclasses(root: type) -> list[type]:
    """Return every concrete subclass of ``root`` (depth-first, dedup by identity).

    Uses ``type.__subclasses__()`` which only yields LIVE subclasses;
    garbage-collected definitions silently drop. That is the correct contract
    for a test-isolation clear -- a definition that has already been collected
    has no binding state to reset.
    """
    seen: set[type] = set()
    result: list[type] = []
    stack: list[type] = list(root.__subclasses__())
    while stack:
        cls = stack.pop()
        if cls in seen:
            continue
        seen.add(cls)
        result.append(cls)
        stack.extend(cls.__subclasses__())
    return result


def _safe_import(module_path: str, attr: str) -> Any:
    """Cycle-safe import of ``module_path.attr`` returning ``None`` on ImportError.

    Encapsulates the "best-effort, skip and continue" pattern the
    ``registry.clear()`` lifecycle relies on: a partial-load environment (one
    submodule reachable, another not) still clears whatever IS reachable. A
    ``None`` entry in ``sys.modules`` (the test-isolation way of simulating an
    unimportable submodule) raises ``ImportError`` here, same as the previous
    inline ``from .submodule import X`` guards.
    """
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return None
    return getattr(module, attr, None)


def clear_generated_input_namespace(
    *,
    materialized_names: dict[str, type],
    field_specs: dict[Any, Any],
    factory_module: str,
    factory_class_name: str,
    collision_registry_attr: str,
    set_module: str,
    set_class_name: str,
) -> None:
    """Reset a family's generated-input ledger and per-set binding state.

    Clears the bookkeeping that prevents stale-state leakage across
    consumer-side autouse-reload fixtures:

    - ``materialized_names`` -- forces the materialization helper to re-emit on
      the next finalize.
    - ``field_specs`` -- per-(set, field) provenance for the runtime normalizer.
    - the arguments factory's class-level caches (``input_object_types`` and the
      family collision registry named by ``collision_registry_attr``).
    - every set subclass's phase-2.5 binding state. The reset attrs come from the
      resolved set base's ``_lifecycle`` descriptor (``SetLifecycleAttrs``) rather
      than a re-spelled tuple, so the family names them in ONE place (the 0.0.9
      DRY pass, ``docs/feedback.md`` Major 3).

    **Materialized class objects are intentionally left parked** in the family
    ``inputs`` module ``__dict__``: the materialization helper overwrites the
    module global via ``setattr`` on the next finalize, so a parked class is
    replaced in place once the rebuild runs. Stripping it via ``delattr`` here
    would break any ``strawberry.lazy(...)`` LazyType held by a consumer module
    whose autouse-reload fixture did NOT also reload the holder.

    Each subsystem lookup is best-effort (``_safe_import``): an unreachable
    factory / set module never prevents the reachable ledger reset. The two
    lookups are independent so a partial-load build state still clears whatever
    is reachable.
    """
    materialized_names.clear()
    field_specs.clear()

    factory_cls = _safe_import(factory_module, factory_class_name)
    if factory_cls is not None:
        factory_cls.input_object_types.clear()
        getattr(factory_cls, collision_registry_attr).clear()

    set_root = _safe_import(set_module, set_class_name)
    if set_root is not None:
        # The per-family binding-state attrs (owner / expansion cache / reentry
        # guard) come from the set base's ``_lifecycle`` descriptor, so the names
        # are not re-spelled at the call site.
        binding_attrs = set_root._lifecycle.binding_attrs
        for subclass in iter_set_subclasses(set_root):
            # ``delattr`` on the subclass so an inherited default (the set
            # base's ``_owner_definition = None``) is restored rather than
            # masked. Each attribute is removed only when set directly on the
            # subclass (``in subclass.__dict__``) so a subclass that never had
            # a binding tolerates the clear.
            for attr in binding_attrs:
                if attr in subclass.__dict__:
                    delattr(subclass, attr)


class GeneratedInputArgumentsFactory:
    """BFS-build every reachable Strawberry input class for a set-family root.

    Shared substrate for ``filters/factories.py::FilterArgumentsFactory`` and
    ``orders/factories.py::OrderArgumentsFactory`` (and the cookbook's parallel
    ``*_arguments_factory.py`` BFS algorithm). The BFS walk, the per-class
    collision check, the idempotent cache, and the subclass-rejection guard are
    single-sited here; each family factory subclasses this DIRECTLY and supplies
    its own caches plus the family hook attributes below.

    Required per-family class attributes:

    - ``input_object_types: dict[str, type]`` -- class-name -> built input
      class. A fresh dict per family (filter and order builds must never share
      a namespace); the base declares it annotation-only so a family that
      forgets to redefine it fails loud at first use rather than sharing.
    - the collision registry named by ``_collision_registry_attr`` -- a fresh
      dict per family. Kept spec-named (``_type_filterset_registry`` /
      ``_type_orderset_registry``) so ``registry.clear()`` and the test suite
      address it directly; the base reaches it through the
      ``_collision_registry`` property.
    - ``_factory_label`` / ``_family_label`` / ``_rename_noun`` -- collision
      error wording so the message still names ``FilterArgumentsFactory`` /
      ``FilterSet`` / ``filterset`` vs the order equivalents.
    - ``_related_attr`` / ``_related_target_attr`` -- the related-collection
      attribute (``related_filters`` / ``related_orders``) and the attribute on
      each related entry that resolves the target set class (``filterset`` /
      ``orderset``).

    Subclassing a CONCRETE family factory is rejected at class-creation time:
    the class-level caches are mutable dicts a grand-subclass would inherit
    rather than isolate, silently cross-contaminating builds. Extend by
    composition (wrap an instance), not inheritance.
    """

    # Per-family caches -- declared annotation-only; each family factory MUST
    # redefine ``input_object_types`` and its named collision registry as fresh
    # dicts. No default here, so a forgetful subclass AttributeErrors loudly
    # instead of silently sharing the base's namespace.
    input_object_types: ClassVar[dict[str, type]]
    _collision_registry_attr: ClassVar[str]
    _factory_label: ClassVar[str]
    _family_label: ClassVar[str]
    _rename_noun: ClassVar[str]
    _related_attr: ClassVar[str]
    _related_target_attr: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Allow the direct family factories; reject any deeper subclassing."""
        super().__init_subclass__(**kwargs)
        # The two family factories subclass this base directly. A class whose
        # bases do NOT include the base is a grand-subclass of a concrete
        # factory -- reject it (its caches would be the family's, not its own).
        if GeneratedInputArgumentsFactory not in cls.__bases__:
            parent = cls.__bases__[0]
            raise TypeError(
                f"{parent.__name__} does not support subclassing "
                f"(attempted by {cls.__name__!r}): its class-level caches are shared "
                "mutable dicts a subclass would inherit rather than isolate, silently "
                "cross-contaminating builds. Extend it by composition (wrap an "
                "instance), not inheritance.",
            )

    def __init__(self, set_class: type) -> None:
        """Store the root set class and its class-derived input type name."""
        self.set_class = set_class
        self.input_type_name = set_class.type_name_for()

    @property
    def _collision_registry(self) -> dict[str, type]:
        """The family collision registry, addressed through its spec-named attr."""
        return getattr(type(self), self._collision_registry_attr)

    @property
    def arguments(self) -> type:
        """BFS-build the root set and return its input class.

        Idempotent: subsequent reads against the same set hit the cache.
        """
        self._ensure_built()
        return self.input_object_types[self.input_type_name]

    def _ensure_built(self) -> None:
        """BFS-walk the root set + every reachable related target.

        Cycles (``A -> B -> A``) are handled naturally by the enqueue-time
        ``target not in seen`` gate. Builds each set exactly once; subsequent
        visits hit the cache. FIFO queue (``pending.pop(0)``) gives a
        deterministic breadth-first build order across both subsystems.
        Collision detection raises when two distinct sets claim the same name.
        """
        pending: list[type] = [self.set_class]
        seen: set[type] = set()
        while pending:
            set_cls = pending.pop(0)
            if set_cls in seen:
                continue
            seen.add(set_cls)

            target_name = set_cls.type_name_for()
            existing_owner = self._collision_registry.get(target_name)
            if existing_owner is not None and existing_owner is not set_cls:
                raise ConfigurationError(
                    f"{self._factory_label}: input type name {target_name!r} is claimed "
                    f"by two distinct {self._family_label} classes: "
                    f"{existing_owner.__module__}.{existing_owner.__qualname__} vs "
                    f"{set_cls.__module__}.{set_cls.__qualname__}. Rename one "
                    f"{self._rename_noun} so its class-derived input type name is unique.",
                )

            if target_name not in self.input_object_types:
                self._build_class_type(set_cls)

            for related in getattr(set_cls, self._related_attr, {}).values():
                target = getattr(related, self._related_target_attr)
                # ``Related*(None, ...)`` placeholder -- skip silently.
                if target is not None and target not in seen:
                    pending.append(target)

    def _build_class_type(self, set_cls: type) -> None:
        """Build the root input class for ``set_cls`` and stash it in the cache."""
        type_name = set_cls.type_name_for()
        owner_definition = getattr(set_cls, "_owner_definition", None)
        triples = self._build_input_triples(set_cls, type_name, owner_definition)
        input_cls = build_strawberry_input_class(type_name, triples)
        self.input_object_types[type_name] = input_cls
        self._collision_registry[type_name] = set_cls

    def _build_input_triples(
        self,
        set_cls: type,
        type_name: str,
        owner_definition: Any,
    ) -> list[tuple[str, Any, dict[str, Any]]]:
        """Return the input-field triples for ``set_cls`` (family hook).

        The filter family appends ``_build_logic_fields`` (the ``and_`` /
        ``or_`` / ``not_`` operator bag); the order family returns the field
        triples as-is (no operator bag, Spec Decision 8).
        """
        raise NotImplementedError  # family hook
