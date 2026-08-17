"""Mixins and lifecycle machinery shared by the ``FilterSet`` and ``OrderSet`` families.

Ported from ``django_graphene_filters/mixins.py`` and refactored to this
package's structure (Strawberry, not Graphene) and dependencies. This module
lives at the package root so the shipped ``filters`` / ``orders`` subpackages
and future ``aggregates`` / ``fieldsets`` subpackages all import shared
set-machinery from one neutral home rather than from each other.

The two foundational mixins the shipped ``FilterSet`` / ``OrderSet`` use:

- ``ClassBasedTypeNameMixin`` -- class-derived GraphQL type naming
  (``type_name_for``), the single naming rule every set's arguments factory
  shares (the cookbook uses it for filterset, orderset, AND aggregateset).
- ``LazyRelatedClassMixin`` -- string / callable class-reference resolution
  used by ``RelatedFilter`` / ``RelatedOrder``.
- ``ActiveInputPermissionMixin`` -- the Decision-8 permission facade
  (``_request_from_info`` / ``_run_permission_checks`` / active-field
  walkers) parameterized by ``ActiveInputPermissionAttrs``. Mechanics live
  in ``utils/permissions.py``; this mixin is the one wrapper layer both
  families used to copy.

Plus the set-family DECLARATION-LIFECYCLE substrate single-sited here, so a
future set family does not copy the related-declaration +
metaclass + expansion lifecycle a fourth time:

- ``RelatedSetTargetMixin`` -- the idempotent owner-bind + lazy target-class
  property machinery, parameterized by the per-family attr names.
- ``collect_related_declarations`` -- the metaclass collect-and-bind step.
- ``expanded_once`` -- the class-level expansion cache + reentry-guard skeleton
  shared by ``FilterSet.get_filters`` / ``OrderSet.get_fields``.
- ``SetLifecycleAttrs`` -- the per-family binding-state descriptor naming the
  ``registry.clear()`` reset attrs (owner / expansion cache / reentry guard) in
  one place instead of re-spelled tuples.

The cookbook's other shared helpers (``get_concrete_field_names``,
``InputObjectTypeFactoryMixin``, ``ObjectTypeFactoryMixin``) are intentionally
NOT ported yet: the shipped sets do not use them today, and the package's
100%-coverage gate would flag them as dead. They land with their consuming
sets.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from django.utils.module_loading import import_string

from .exceptions import ConfigurationError
from .utils.input_values import is_inactive_value
from .utils.permissions import (
    active_permission_targets,
    active_related_branches,
    extract_branch_value,
    invoke_permission_method,
    request_from_info,
    run_active_input_permission_checks,
    verbatim_path,
)
from .utils.strings import pascal_case_or_raise


class ClassBasedTypeNameMixin:
    """Contribute a ``type_name_for()`` classmethod for class-derived GraphQL naming.

    Subclasses tune two class attributes:

    - ``_root_type_suffix`` -- appended to ``cls.__name__`` for the root type
      (``FilterSet`` keeps the default ``"InputType"`` -> ``FooFilterInputType``).
    - ``_field_type_suffix`` -- appended after a PascalCased field path for the
      per-field operator-bag type (``FilterSet`` overrides to
      ``"FilterInputType"`` -> ``FooFilterBarFilterInputType``).

    A single implementation handles both the root name (``field_path is None``)
    and a ``LOOKUP_SEP``-separated nested path. Centralising it here means the
    shipped ``OrderSet`` and future ``AggregateSet`` reuse the exact same naming
    rule with their own suffixes instead of re-deriving the convention inline.

    Port of ``django_graphene_filters/mixins.py::ClassBasedTypeNameMixin``,
    using this package's ``utils.strings.pascal_case_or_raise`` in place of
    the cookbook's ``stringcase.pascalcase``.
    """

    _root_type_suffix: str = "InputType"
    _field_type_suffix: str = "InputType"

    @classmethod
    def type_name_for(cls, field_path: str | None = None) -> str:
        """Return the GraphQL type name for this class, or for a sub-field path.

        Raises ``ConfigurationError`` when ``field_path`` contains no
        word-character tokens (e.g. ``""``, ``"_"``, ``"__"``); without the
        guard the per-field segment would silently collapse to an empty
        string and the resulting type name would collide with the root
        ``f"{cls.__name__}{cls._root_type_suffix}"`` (or with a sibling
        field's bag class). The conversion + guard are the shared
        ``utils.strings.pascal_case_or_raise`` (shared with
        ``filters/inputs.py::_pascal_case``); ``pascal_case`` splits on
        ``"_"`` and drops empty tokens, so a ``LOOKUP_SEP`` (``"__"``)
        boundary PascalCases each path segment exactly as the previous
        per-segment split did. Raising here surfaces the real cause at the
        call site for every consumer (``_build_input_fields`` operator-bag
        naming, shipped ``OrderSet`` and future ``AggregateSet`` per-field
        naming).
        """
        if field_path is None:
            return f"{cls.__name__}{cls._root_type_suffix}"
        pascal = pascal_case_or_raise(
            field_path,
            make_error=lambda bad: ConfigurationError(
                f"{cls.__name__}.type_name_for received field_path {bad!r} "
                "which contains no word characters; rename the filter / field so "
                "its name has at least one alphanumeric token.",
            ),
        )
        return f"{cls.__name__}{pascal}{cls._field_type_suffix}"


class LazyRelatedClassMixin:
    """Resolve a class reference that may be a string, callable, or class.

    Port of `django_graphene_filters/mixins.py::LazyRelatedClassMixin`; the
    ``resolve_lazy_class`` body is byte-equivalent to upstream while the
    class docstring is rewritten to surface the consumer-side rationale.
    Used by `RelatedFilter` to break cycles between filtersets declared in
    the same module without forcing an `if TYPE_CHECKING` dance on the
    consumer.
    """

    def resolve_lazy_class(self, class_ref: Any, bound_class: type | None) -> Any:
        """Resolve `class_ref` to a class.

        Strings resolve via two attempts:

        1. As an absolute import path through `import_string`.
        2. On `ImportError`, prefixed with `bound_class.__module__` so an
           unqualified `"ManagerFilter"` resolves against the owning
           filterset's module.

        If attempt 1 raises and `bound_class` is `None` (or otherwise
        falsy), the original `ImportError` propagates unchanged.

        Callables that are not classes are invoked as zero-arg factories;
        everything else is returned as-is.
        """
        if isinstance(class_ref, str):
            try:
                return import_string(class_ref)
            except ImportError:
                if bound_class:
                    path = f"{bound_class.__module__}.{class_ref}"
                    return import_string(path)
                raise
        elif callable(class_ref) and not isinstance(class_ref, type):
            return class_ref()
        return class_ref


class RelatedSetTargetMixin(LazyRelatedClassMixin):
    """Idempotent owner-bind + lazy target-class resolution for a related-set declaration.

    The machinery ``RelatedFilter`` / ``RelatedOrder`` grew as byte-parallel
    copies: an idempotent ``bind_*`` that records
    the owning set ONCE (a second, possibly divergent, bind is a no-op - strict
    cross-owner mismatch is caught later at finalize), and a lazy ``.<target>``
    property that resolves a string / callable target through
    ``resolve_lazy_class`` and re-stores the result so the next access is a plain
    read.

    Parameterized by two instance-attribute names a subclass sets as class
    attributes:

    - ``_target_attr`` -- the slot holding the possibly-lazy target
      (``"_filterset"`` / ``"_orderset"``).
    - ``_owner_attr`` -- the slot the bind records the owner under, and the
      resolution scope for an unqualified string target
      (``"bound_filterset"`` / ``"bound_orderset"``).

    Subclasses keep their family-named public surface (``bind_filterset`` +
    ``.filterset`` / ``bind_orderset`` + ``.orderset``) as thin wrappers over
    ``_bind_owner`` / ``_resolved_target`` / ``_set_target``, so the public
    ``RelatedFilter`` / ``RelatedOrder`` attributes are unchanged.
    """

    _target_attr: str
    _owner_attr: str

    def _bind_owner(self, owner: type) -> None:
        """Bind the owning set once; a second (possibly divergent) bind is a no-op."""
        if not hasattr(self, self._owner_attr):
            setattr(self, self._owner_attr, owner)

    def _resolved_target(self) -> Any:
        """Resolve the (possibly-lazy) target class on first access and re-store it."""
        resolved = self.resolve_lazy_class(
            getattr(self, self._target_attr),
            getattr(self, self._owner_attr, None),
        )
        setattr(self, self._target_attr, resolved)
        return resolved

    def _set_target(self, value: Any) -> None:
        """Substitute the target class (the ``.<target>`` setter seam)."""
        setattr(self, self._target_attr, value)


def collect_related_declarations(
    new_class: type,
    bases: tuple,
    *,
    own_items: Any,
    declaration_type: type,
    collection_attr: str,
    inherit_from_bases: bool,
    class_items: Any | None = None,
    base_declarations_attr: str | None = None,
) -> OrderedDict:
    """Collect a metaclass's related-set declarations onto ``new_class`` and bind each.

    The shared ``FilterSetMetaclass`` / ``OrderSetMetaclass`` collect-and-bind
    step: build an ``OrderedDict`` of the
    ``declaration_type`` instances, store it on ``new_class`` under
    ``collection_attr``, and call each declaration's ``_bind_owner(new_class)``
    (the ``RelatedSetTargetMixin`` idempotent owner bind).

    ``inherit_from_bases`` selects the MRO-merge policy:

    - ``False`` (filter side): ``own_items`` is ``declared_filters.items()``,
      whose upstream MRO merge establishes the candidate order before the final
      precedence reconciliation below.
    - ``True`` (order side): the plain ``type`` metaclass does no merge, so each
      base's existing ``collection_attr`` is copied first (reverse iteration lets
      earlier bases override later ones, matching Python's MRO) and then
      ``own_items`` (the class body's ``attrs``) override inherited same-named
      declarations.

    A non-declaration class attribute shadows and removes an inherited declaration.
    The final base-precedence reconciliation also preserves that removal through
    diamond inheritance: an earlier base's tombstone must not let a declaration
    from a later base reappear. ``class_items`` preserves the raw class body when
    an upstream metaclass mutates it, while ``base_declarations_attr`` identifies
    that family's complete declaration map (including non-related declarations).
    """
    own_items = tuple(own_items)
    class_values = dict(own_items if class_items is None else class_items)
    base_declarations_attr = base_declarations_attr or collection_attr

    collected: OrderedDict = OrderedDict()
    if inherit_from_bases:
        for base in reversed(bases):
            for name, declaration in getattr(base, collection_attr, {}).items():
                collected[name] = declaration
    for name, declaration in own_items:
        if isinstance(declaration, declaration_type):
            collected[name] = declaration
        elif name in collected:
            del collected[name]

    # Resolve every inherited candidate against direct-base precedence. A base
    # with the name in its complete declaration map owns that slot; otherwise a
    # normal class attribute anywhere in that base's MRO is a tombstone. This
    # catches the diamond case that a flattened declaration map cannot represent.
    missing = object()
    for name in tuple(collected):
        if name in class_values:
            continue
        for base in bases:
            declarations = getattr(base, base_declarations_attr, {})
            if name in declarations:
                selected = declarations[name]
                if isinstance(selected, declaration_type):
                    collected[name] = selected
                else:
                    del collected[name]
                break
            inherited_value = next(
                (
                    ancestor.__dict__[name]
                    for ancestor in base.__mro__
                    if name in ancestor.__dict__
                ),
                missing,
            )
            if inherited_value is not missing:
                del collected[name]
                break
    setattr(new_class, collection_attr, collected)
    for declaration in collected.values():
        declaration._bind_owner(new_class)
    return collected


def expanded_once(
    cls: type,
    *,
    cache_attr: str,
    guard_attr: str,
    build: Callable[[], Any],
    on_reentry: Callable[[], Any] | None = None,
) -> Any:
    """Run ``build()`` once under a class-level expansion cache + reentry guard.

    The control-flow skeleton ``FilterSet.get_filters`` / ``OrderSet.get_fields``
    grew separately:

    - Return ``cls.__dict__[cache_attr]`` when populated. Read from the class's
      OWN ``__dict__`` (NOT ``getattr``) so a subclass never inherits a parent's
      completed expansion cache via MRO, and so an in-flight class (the metaclass
      runs ``super().__new__`` -> ``get_filters`` before stamping
      ``related_filters``) cannot serve a half-built result.
    - ``on_reentry`` (filter side only): when set AND ``cls`` is already mid-
      expansion (``guard_attr`` truthy in its own ``__dict__``), return
      ``on_reentry()`` -- the unexpanded fallback that breaks a self-referential
      ``RelatedFilter`` cycle without caching a half-built result. The order side
      passes ``None`` (its expansion never re-enters ``get_fields``).
    - Otherwise set ``guard_attr`` ``True`` on ``cls``, run ``build()`` (which
      owns the family-specific expansion AND the cache-write decision, including
      any family side-effect such as ``FilterSet.base_filters``), and clear the
      guard in a ``finally``.

    Single-threaded contract: ``guard_attr`` is a class-level flag, not a
    thread-local one. Expansion runs during ``finalize_django_types()``
    (single-threaded) and once per class; parallel test runs that exercise the
    same set class from different threads can race the flag (the second thread
    short-circuits via ``on_reentry`` to the unexpanded set). Do not introduce a
    ``threading.local`` here without a real consumer call path requiring it.
    """
    cached = cls.__dict__.get(cache_attr)
    if cached is not None:
        return cached
    if on_reentry is not None and cls.__dict__.get(guard_attr, False):
        return on_reentry()
    setattr(cls, guard_attr, True)
    try:
        return build()
    finally:
        setattr(cls, guard_attr, False)


def should_cache_expansion(cls: type, *, related_attr: str, target_slot: str) -> bool:
    """Return whether a set class's expansion result may be cached.

    The two-condition cache-write gate ``FilterSet.get_filters`` and
    ``OrderSet.get_fields`` grew separately, single-sited beside
    ``expanded_once`` so the string-lazy-target rule (a CORRECTNESS rule:
    caching too early pins a half-resolved expansion) has one owner. Cache only
    when:

    1. ``related_attr`` (``related_filters`` / ``related_orders``) is on this
       class's OWN ``__dict__`` - not inherited from the family base, which
       carries the empty ``OrderedDict`` the metaclass sets on the in-flight
       class AFTER ``super().__new__`` returns; and
    2. every related entry's ``target_slot`` (``_filterset`` / ``_orderset``)
       is a real class - no unresolved string forward references remain.
    """
    return related_attr in cls.__dict__ and all(
        not isinstance(getattr(entry, target_slot), str)
        for entry in getattr(cls, related_attr).values()
    )


@dataclass(frozen=True)
class SetLifecycleAttrs:
    """The class-level lifecycle attribute names a set family resets / caches under.

    Single source for the attr-name strings otherwise re-spelled across a
    family's class body, its ``get_filters`` / ``get_fields`` expansion, and the
    ``registry.clear()`` binding-state reset (the tuple
    ``utils/inputs.py::clear_generated_input_namespace`` consumes). Each family
    declares ONE instance on its set class.
    """

    owner: str  # the finalizer-bound owner-definition slot (``_owner_definition``).
    cache: (
        str  # the completed-expansion cache slot (``_expanded_filters`` / ``_expanded_fields``).
    )
    guard: str  # the expansion reentry-guard slot (``_is_expanding_filters`` / ``_is_expanding_fields``).
    # Family-specific EXTRA class-level slots published atomically alongside the
    # expansion cache (empty for the order family). The filter family adds its
    # candidate-metadata expansion-snapshot slot here so ``registry.clear()``
    # resets filters and metadata TOGETHER, by construction: a free-floating
    # fourth class attribute would survive the clear that deletes ``cache`` and
    # pair stale metadata with a rebuilt ``base_filters``.
    extra: tuple[str, ...] = ()

    @property
    def binding_attrs(self) -> tuple[str, ...]:
        """The ``(owner, cache, guard, *extra)`` tuple ``clear_generated_input_namespace`` resets."""
        return (
            self.owner,
            self.cache,
            self.guard,
            *self.extra,
        )


@dataclass(frozen=True)
class ActiveInputPermissionAttrs:
    """Per-family configuration for ``ActiveInputPermissionMixin``.

    The permission *mechanics* are single-sited in ``utils/permissions.py``.
    What used to be re-spelled on ``FilterSet`` and ``OrderSet`` as twin
    thin wrappers is the family shape: which related collection to walk,
    which child-set attribute to recurse through, which field-spec map
    supplies ``django_source_path``, whether the input is a top-level list
    (order) or a struct with ``UNSET`` defaults (filter), and the GraphQL
    family label ``request_from_info`` puts in ``ConfigurationError``.
    """

    family_label: str
    related_attr: str
    target_attr: str
    field_specs: Mapping[Any, Any]
    logic_keys: frozenset[str] = frozenset()
    unset_sentinel: Any = None
    handle_top_level_list: bool = False


class ActiveInputPermissionMixin:
    """Decision-8 permission facade shared by ``FilterSet`` and ``OrderSet``.

    Subclasses declare one ``_permission: ActiveInputPermissionAttrs`` and
    inherit the request / branch / active-field / invoke / run surface that
    ``run_active_input_permission_checks`` re-enters. Family-only work stays
    on overridable hooks:

    - ``_permission_fallback_path`` -- filter remaps lookup attrs to form
      keys; order uses the python attr verbatim.
    - ``_check_permission_depth`` -- filter caps logical-branch nesting;
      order has no operator bag, so the default is a no-op (related
      recursion is already capped inside ``run_active_input_permission_checks``).
    - ``_run_logic_permission_checks`` -- filter recurses ``and`` / ``or`` /
      ``not``; order has none.

    Apply pipelines stay family-owned: filters still derive related
    visibility and validate a django-filter form; orders still flatten to
    ``OrderBy``. Those contracts do not share a driver.
    """

    _permission: ClassVar[ActiveInputPermissionAttrs]

    @classmethod
    def _request_from_info(cls, info: Any) -> Any:
        """Resolve the Django request from ``info.context``.

        Thin delegate to ``utils/permissions.py::request_from_info``.
        """
        return request_from_info(info, family_label=cls._permission.family_label)

    @classmethod
    def _extract_branch_value(cls, input_value: Any, field_name: str) -> Any:
        """Return the value at ``field_name`` on a dataclass-or-dict input.

        Thin delegate to ``utils/permissions.py::extract_branch_value`` with
        this family's ``unset_sentinel``.
        """
        return extract_branch_value(
            input_value,
            field_name,
            unset_sentinel=cls._permission.unset_sentinel,
        )

    @classmethod
    def _iter_active_related_branches(cls, input_value: Any) -> list[tuple[str, Any, Any]]:
        """List ``(field_name, related_obj, child_input)`` for present branches.

        Thin delegate to ``utils/permissions.py::active_related_branches``.
        """
        cfg = cls._permission
        return active_related_branches(
            cls,
            input_value,
            related_attr=cfg.related_attr,
            unset_sentinel=cfg.unset_sentinel,
            handle_top_level_list=cfg.handle_top_level_list,
        )

    @staticmethod
    def _invoke_permission_method(
        bare_instance: Any,
        field_path: str,
        request: Any,
        *,
        fired: set[str] | None = None,
    ) -> None:
        """Call ``check_<field_path>_permission(request)`` if defined.

        Thin delegate to ``utils/permissions.py::invoke_permission_method``.
        """
        invoke_permission_method(bare_instance, field_path, request, fired=fired)

    @staticmethod
    def _permission_fallback_path(python_attr: str) -> str:
        """Map a python attr to its permission source path when no field-spec exists.

        Default: the attr IS the path (order side). ``FilterSet`` remaps
        lookup attrs onto django-filter form keys.
        """
        return verbatim_path(python_attr)

    @classmethod
    def _active_permission_field_paths(cls, input_value: Any) -> list[str]:
        """Return the base Django source path for each active top-level leaf.

        Thin delegate to ``_active_permission_targets``'s ``LEAF`` half.
        """
        return cls._active_permission_targets(input_value)[0]

    @classmethod
    def _active_permission_targets(
        cls,
        input_value: Any,
    ) -> tuple[list[str], list[tuple[str, Any, Any]]]:
        """Single-pass ``(leaf source paths, active related branches)`` for one level.

        Thin delegate to ``utils/permissions.py::active_permission_targets``.
        """
        cfg = cls._permission
        return active_permission_targets(
            cls,
            input_value,
            field_specs=cfg.field_specs,
            related_attr=cfg.related_attr,
            logic_keys=cfg.logic_keys,
            fallback_path=cls._permission_fallback_path,
            unset_sentinel=cfg.unset_sentinel,
            handle_top_level_list=cfg.handle_top_level_list,
        )

    @classmethod
    def _check_permission_depth(cls, _depth: int) -> None:
        """Cap family-specific nesting. Default no-op; ``FilterSet`` overrides."""
        return

    @classmethod
    def _run_logic_permission_checks(
        cls,
        _input_value: Any,
        _request: Any,
        *,
        _fired: dict[type, set[str]],
        _bare: Any,
        _depth: int,
    ) -> None:
        """Recurse into family-specific logical containers. Default no-op."""
        return

    @classmethod
    def _prepare_permission_input(cls, _input_value: Any) -> None:
        """Populate family-specific provenance before traversal. Default no-op.

        A direct ``apply`` / permission call can reach the facade before the
        family's field-spec ledger has been built for this class, so the
        traversal would read empty provenance. Families that build their specs
        lazily populate them here; the facade itself stays single-sourced.
        """
        return

    @classmethod
    def _run_permission_checks(
        cls,
        input_value: Any,
        request: Any,
        *,
        _fired: dict[type, set[str]] | None = None,
        _bare: Any = None,
        _depth: int = 0,
    ) -> None:
        """Fire ``check_<field>_permission(request)`` for fields in the input.

        Active-input-only: a declared ``check_*`` gate that is not exercised
        by this call leaves the queryset untouched. Recurses into each
        active related branch so the cookbook's nested-permission contract
        holds. Filter-only logical ``and`` / ``or`` / ``not`` recursion is
        the ``_run_logic_permission_checks`` hook. Family provenance that the
        traversal depends on is populated first via
        ``_prepare_permission_input``.
        """
        cls._prepare_permission_input(input_value)
        if is_inactive_value(input_value, unset_sentinel=cls._permission.unset_sentinel):
            return
        cls._check_permission_depth(_depth)
        if _fired is None:
            _fired = {}
        bare = _bare if _bare is not None else object.__new__(cls)
        cfg = cls._permission
        run_active_input_permission_checks(
            cls,
            input_value,
            request,
            fired=_fired,
            bare=bare,
            target_attr=cfg.target_attr,
            related_attr=cfg.related_attr,
            depth=_depth,
        )
        cls._run_logic_permission_checks(
            input_value,
            request,
            _fired=_fired,
            _bare=bare,
            _depth=_depth,
        )


__all__ = (
    "ActiveInputPermissionAttrs",
    "ActiveInputPermissionMixin",
    "ClassBasedTypeNameMixin",
    "LazyRelatedClassMixin",
    "RelatedSetTargetMixin",
    "SetLifecycleAttrs",
    "collect_related_declarations",
    "expanded_once",
)
