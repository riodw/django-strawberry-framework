"""``OrderSetMetaclass`` (Layer 3) and ``OrderSet`` foundation (Layer 4).

The metaclass is a verbatim port of
``django_graphene_filters/orderset.py::OrderSetMetaclass``; ``OrderSet``
mixes the cookbook's cycle-safe ``get_fields`` (the Layer-4 expansion)
over ``ClassBasedTypeNameMixin`` from ``..sets_mixins``.

Slice 1 shipped the class skeleton + ``get_fields()`` Layer-4 expansion
with the ``"__all__"`` branch raising ``NotImplementedError``. Slice 2
expands the file to:

- Replace the ``"__all__"`` placeholder with the
  ``_get_concrete_field_names_for_order`` walk per spec-028 Revision 4 B4.
- Add the resolver-facing classmethod pair ``apply_sync`` /
  ``apply_async`` (no ``apply(...)`` dispatcher per Spec DoD 4(c)).
- Add the ``check_permissions`` instance method + the classmethod
  pipeline (``_run_permission_checks`` / ``_active_permission_field_paths``
  / ``_iter_active_related_branches`` / ``_invoke_permission_method`` /
  ``_request_from_info``) that drives active-input-only per-field
  ``check_<field>_permission`` dispatch per Spec Decision 8 step 6.
- Add the cookbook-style ``get_flat_orders`` classmethod walking the
  normalized data structure.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any

from django.db import models
from django.http import HttpRequest

from ..exceptions import ConfigurationError
from ..sets_mixins import ClassBasedTypeNameMixin
from .base import RelatedOrder
from .inputs import Ordering, _field_specs, normalize_input_value

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from ..types.definition import DjangoTypeDefinition


class OrderSetMetaclass(type):
    """Discover ``RelatedOrder`` declarations and bind them to the new class.

    Direct port of
    ``django_graphene_filters/orderset.py::OrderSetMetaclass``. Inherited
    ``related_orders`` are collected in MRO order with the current class's
    own declarations overriding same-named inherited ones (standard Python
    MRO semantics); every collected ``RelatedOrder`` is bound back to the
    new class via ``bind_orderset``.
    """

    def __new__(
        cls: type[OrderSetMetaclass],
        name: str,
        bases: tuple,
        attrs: dict,
    ) -> OrderSetMetaclass:
        """Build the class, collect ``RelatedOrder`` declarations, bind owner."""
        new_class = super().__new__(cls, name, bases, attrs)

        # Start with inherited related_orders from base classes (in MRO order,
        # with later bases overriding earlier ones — matches Python's method
        # resolution). Cookbook lines 30-33.
        inherited: OrderedDict = OrderedDict()
        for base in reversed(bases):
            for n, f in getattr(base, "related_orders", {}).items():
                inherited[n] = f

        # Apply the current class's own declarations, overriding inherited
        # ones. Cookbook lines 36-38.
        for n, f in attrs.items():
            if isinstance(f, RelatedOrder):
                inherited[n] = f

        new_class.related_orders = inherited
        for f in new_class.related_orders.values():
            f.bind_orderset(new_class)
        return new_class


class OrderSet(ClassBasedTypeNameMixin, metaclass=OrderSetMetaclass):
    """Consumer-facing ``OrderSet`` foundation.

    Layer-3 + Layer-4 + resolver-API port of
    ``django_graphene_filters/orderset.py::AdvancedOrderSet``. Inherits
    ``type_name_for`` from ``ClassBasedTypeNameMixin`` (the shared
    ``{cls.__name__}InputType`` naming rule) and gets its
    ``related_orders`` collection via ``OrderSetMetaclass``.

    The resolver-facing surface is the classmethod pair ``apply_sync`` /
    ``apply_async`` per spec-028 Decision 8 step 7. Each carries ``info``
    end-to-end so per-field ``check_<field>_permission`` gates and
    active-input-only scope run consistently. There is **no**
    ``apply(...)`` dispatcher (Spec DoD 4(c) -- the filter side's
    ``apply`` exists to translate a sync-misuse ``RuntimeError`` raised
    when a ``RelatedFilter`` target declares an async ``get_queryset``;
    the order side has no equivalent code path).

    The order side does NOT override ``_field_type_suffix`` -- the
    cookbook's upstream ``AdvancedOrderSet`` keeps the default
    ``"InputType"`` for both root and per-field suffixes (the cookbook
    declares both explicitly at the same value; this port relies on the
    mixin defaults instead). This is the deliberate divergence from
    ``FilterSet`` (which overrides to ``"FilterInputType"`` for the
    per-field operator-bag types); the order side has no per-field
    operator bag.
    """

    # Binding seam — populated by ``finalize_django_types`` phase 2.5 in
    # Slice 3 per spec-028 Decision 6. The slot's existence is the Slice 1
    # contract; the binding write lands in Slice 3. Same shape as the
    # filter side's ``FilterSet._owner_definition``.
    _owner_definition: DjangoTypeDefinition | None = None

    # Cache for fully-resolved fields per Layer 4 of spec-028 Decision 3.
    _expanded_fields = None
    # Recursion guard around ``get_fields`` so a self-referential
    # ``RelatedOrder`` does not blow the stack. The slot stays in place
    # for future defensive use even though the Slice 2 expansion removes
    # the explicit reentry-branch test from ``_expand_meta_fields`` (per
    # the planning-pass disposition -- the branch was structurally
    # unreachable through the planned Slice 2 surface).
    _is_expanding_fields = False

    @classmethod
    def get_fields(cls) -> OrderedDict:
        """Return ``Meta.fields`` expansion merged with ``related_orders``.

        Direct port of
        ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields``
        (cookbook lines 265-285) with the same two-condition cache write
        gate the filter side uses at ``FilterSet.get_filters``:

        - ``cls.__dict__.get("_expanded_fields")`` is checked directly
          (NOT via ``getattr``) so a subclass does not inherit a parent's
          completed cache via MRO.
        - the cache is only written when ``related_orders`` is on this
          class's ``__dict__`` AND every ``_orderset`` is a real class
          (no unresolved string forward references remain).

        ``Meta.fields = "__all__"`` expands via
        ``_get_concrete_field_names_for_order`` (Slice 2's deliverable
        per spec-028 Decision 3 / Revision 4 B4).
        """
        if cls.__dict__.get("_expanded_fields") is not None:
            return cls.__dict__["_expanded_fields"]

        cls._is_expanding_fields = True
        try:
            fields = cls._expand_meta_fields()
            for k, v in getattr(cls, "related_orders", {}).items():
                fields[k] = v

            # Cache only when both conditions hold:
            # 1. ``related_orders`` is on this class (not inherited from
            #    ``OrderSet`` itself, which carries the empty OrderedDict
            #    ``OrderSetMetaclass.__new__`` set on the in-flight class).
            # 2. Every ``_orderset`` is a real class (no unresolved string
            #    forward references remain).
            if "related_orders" in cls.__dict__ and all(
                not isinstance(f._orderset, str) for f in cls.related_orders.values()
            ):
                cls._expanded_fields = fields
            return fields
        finally:
            cls._is_expanding_fields = False

    @classmethod
    def _expand_meta_fields(cls) -> OrderedDict:
        """Expand ``Meta.fields`` into an ``OrderedDict`` keyed by field name.

        Supports list / tuple form (``["title", "subtitle"]``) and the
        ``"__all__"`` shorthand (every column-backed model field name
        per spec-028 Revision 4 B4 -- forward FK columns are included,
        M2M managers and reverse FKs are excluded).
        """
        fields: OrderedDict = OrderedDict()
        meta = getattr(cls, "Meta", None)
        if meta is None:
            return fields
        meta_fields = getattr(meta, "fields", None)
        if meta_fields is None:
            return fields
        if meta_fields == "__all__":
            # Local import dodges any circular-import risk between
            # ``orders/sets.py`` and ``orders/inputs.py`` (the
            # ``_build_input_fields`` adapter imports ``OrderSet`` from
            # ``.sets``; this local import keeps the runtime cycle inert).
            from .inputs import _get_concrete_field_names_for_order

            model = getattr(meta, "model", None)
            if model is None:
                raise ConfigurationError(
                    f"{cls.__name__}.Meta.fields = '__all__' requires Meta.model "
                    "so the column-backed field names can be derived from "
                    "model._meta.get_fields().",
                )
            for name in _get_concrete_field_names_for_order(model):
                fields[name] = None
            return fields
        # Cookbook line 279-280: "Works for both dict (iterates keys) and
        # list/tuple (iterates values)." Order's ``Meta.fields`` is
        # list-only per spec-028 Decision 3 Layer 4, but the iteration
        # pattern works either way.
        for k in meta_fields:
            fields[k] = None
        return fields

    # ------------------------------------------------------------------
    # Resolver-facing API (Slice 2 / spec-028 Decision 8)
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_input(cls, input_value: Any) -> list[tuple[str, Ordering | None]]:
        """Delegate to ``normalize_input_value`` so callers see one entry point.

        Thin classmethod-shaped delegate kept for parity with
        ``FilterSet._normalize_input``. The filter side's classmethod
        returns a dict (form-data shape); the order side returns a
        flat ``[(field_path, Ordering | None), ...]`` list because the
        order pipeline produces ``OrderBy`` expressions directly rather
        than threading form-data through ``django-filter``'s form
        machinery.
        """
        return normalize_input_value(cls, input_value)

    @classmethod
    def _request_from_info(cls, info: Any) -> Any:
        """Resolve the Django request from ``info.context``.

        Canonical Strawberry-Django shape: ``info.context.request``. The
        wrapper-less alternative ``isinstance(info.context, HttpRequest)``
        is detected so consumers running a bare-HttpRequest context (the
        Django test client default) work without bespoke wiring. Any
        other shape raises ``ConfigurationError``. Mirror of
        ``FilterSet._request_from_info``.
        """
        context = getattr(info, "context", None)
        if context is None:
            raise ConfigurationError(
                "OrderSet.apply requires `info.context`; received `info` without a context.",
            )
        request = getattr(context, "request", None)
        if request is not None:
            return request
        if isinstance(context, HttpRequest):
            return context
        raise ConfigurationError(
            f"OrderSet.apply could not resolve a Django HttpRequest from `info.context` "
            f"(got {type(context).__name__}). Expected `info.context.request` or a bare "
            "HttpRequest.",
        )

    @staticmethod
    def _extract_branch_value(input_value: Any, field_name: str) -> Any:
        """Return the value at ``field_name`` on a dataclass-or-dict input.

        Collapses ``None`` to "branch not supplied" so the active-branch
        caller treats absent branches uniformly. Mirror of
        ``FilterSet._extract_branch_value`` minus the
        ``strawberry.UNSET`` collapse -- order inputs default unsupplied
        fields to ``None`` rather than UNSET (the apply pipeline never
        sees an UNSET sentinel from the resolver layer because the
        ``order_input_type`` argument shape is ``list[<T>!] | None``,
        not a struct of UNSET-defaulted attributes).
        """
        if input_value is None:
            return None
        if isinstance(input_value, dict):
            value = input_value.get(field_name)
        else:
            value = getattr(input_value, field_name, None)
        return value

    @classmethod
    def _iter_active_related_branches(
        cls,
        input_value: Any,
    ) -> list[tuple[str, RelatedOrder, Any]]:
        """List ``(field_name, related_order, child_input)`` for present branches.

        Active-branch scoping (spec-028 Decision 8 step 6 / Revision 4
        H3) -- a ``RelatedOrder`` is "active" when its key is present in
        the input. Inactive branches are skipped end-to-end (permission
        recursion and child-orderset normalization) so an empty branch
        does not exercise the child's per-field gates.
        """
        related_orders = getattr(cls, "related_orders", {})
        if not related_orders:
            return []
        active: list[tuple[str, RelatedOrder, Any]] = []
        # Walk each dataclass element of a top-level list separately so
        # the parent gate fires once per active branch occurrence (the
        # ``_fired`` dedup map keys on class, so repeated occurrences
        # collapse to one fire-per-class).
        if isinstance(input_value, list):
            for element in input_value:
                active.extend(cls._iter_active_related_branches(element))
            return active
        for field_name, related_order in related_orders.items():
            child_input = cls._extract_branch_value(input_value, field_name)
            if child_input is None:
                continue
            active.append((field_name, related_order, child_input))
        return active

    @classmethod
    def _active_permission_field_paths(cls, input_value: Any) -> list[str]:
        """Return the base django source path for each active top-level leaf.

        Drives ``_run_permission_checks``'s per-field gate dispatch.
        Emits one entry per supplied leaf field -- its
        ``django_source_path`` -- so ``check_<field>_permission`` fires
        once for a field regardless of which input list element
        populates it. ``RelatedOrder`` branches are excluded here (they
        fire via the related-branch loop); ``None`` attribute values are
        skipped (active-input-only contract).
        """
        if input_value is None:
            return []
        if isinstance(input_value, list):
            # Aggregate across every top-level dataclass element; the
            # caller's ``_fired`` dedup ensures one gate-fire per
            # (class, method-name) pair.
            paths: list[str] = []
            for element in input_value:
                paths.extend(cls._active_permission_field_paths(element))
            return paths
        dataclass_fields = getattr(input_value, "__dataclass_fields__", None)
        if dataclass_fields is None and not isinstance(input_value, dict):
            return []
        if isinstance(input_value, dict):
            items = list(input_value.items())
        else:
            items = [(name, getattr(input_value, name)) for name in dataclass_fields]
        related_keys = set(getattr(cls, "related_orders", {}) or {})
        paths = []
        for python_attr, raw_value in items:
            if raw_value is None:
                continue
            if python_attr in related_keys:
                continue
            spec = _field_specs.get((cls, python_attr))
            if spec is None:
                # Defensive -- before Slice 3's bind, ``_field_specs`` may
                # be empty when permission checks are invoked outside the
                # apply pipeline. Fall back to the python-attr token.
                paths.append(python_attr)
            else:
                paths.append(spec.django_source_path)
        return paths

    @staticmethod
    def _invoke_permission_method(
        bare_instance: Any,
        field_path: str,
        request: Any,
        *,
        fired: set[str] | None = None,
    ) -> None:
        """Call ``check_<field_path>_permission(request)`` if defined.

        When ``fired`` is supplied, the method-name is recorded after a
        successful fire and subsequent calls with the same name skip
        the attribute lookup entirely. The dedup is scoped to the
        supplied set -- ``_run_permission_checks`` passes the per-class
        set keyed out of its shared ``_fired`` map. Mirror of
        ``FilterSet._invoke_permission_method``.
        """
        method_name = f"check_{field_path.replace('__', '_')}_permission"
        if fired is not None and method_name in fired:
            return
        method = getattr(bare_instance, method_name, None)
        if callable(method):
            method(request)
            if fired is not None:
                fired.add(method_name)

    @classmethod
    def _run_permission_checks(
        cls,
        input_value: Any,
        request: Any,
        *,
        _fired: dict[type, set[str]] | None = None,
        _bare: Any = None,
    ) -> None:
        """Fire ``check_<field>_permission(request)`` for fields in the input.

        Active-input-only per spec-028 Decision 8 step 6 -- a declared
        ``check_*`` gate that is not exercised by this call leaves the
        queryset untouched. Recurses into the child orderset for each
        active ``RelatedOrder`` branch so the cookbook's
        nested-permission contract holds.

        The order side has NO ``and`` / ``or`` / ``not`` operator-bag
        recursion -- spec-028 Decision 8 line 686 ("no operator-bag, no
        form validation"). The filter side's depth-counter recursion
        cap has no analogue here either: only the related-branch
        recursion remains, and it terminates naturally at the depth of
        the consumer's declared ``RelatedOrder`` chain.

        Permission methods are called via a bare instance allocated
        with ``object.__new__(cls)``; this matches the cookbook
        contract (per-field gates are written as regular
        ``def check_X_permission(self, request)`` methods) without
        requiring a fully-constructed ``OrderSet`` instance.

        Dedup contract: ``_fired`` maps each ``OrderSet`` class to the
        set of ``check_*_permission`` method names that have already
        fired against THAT class in this top-level call. Shared across
        the related-branch recursion (different classes), so a gate
        fires at most once per class regardless of how many input list
        elements reference the same field path.

        Double-dispatch contract: for an active ``RelatedOrder`` branch
        named ``shelf`` both gates fire -- the parent's
        ``check_shelf_permission`` (the per-branch gate on the owning
        orderset) AND the child orderset's own ``check_*_permission``
        gates. They live in different per-class dedup sets, so both
        fire once.
        """
        if input_value is None:
            return
        if _fired is None:
            _fired = {}
        class_fired = _fired.setdefault(cls, set())
        bare = _bare if _bare is not None else object.__new__(cls)

        for field_path in cls._active_permission_field_paths(input_value):
            cls._invoke_permission_method(bare, field_path, request, fired=class_fired)

        for field_name, related_order, child_input in cls._iter_active_related_branches(
            input_value,
        ):
            child_orderset = related_order.orderset
            if child_orderset is not None and hasattr(child_orderset, "_run_permission_checks"):
                # Child orderset is a different class; it keys its own
                # per-class set inside the shared ``_fired`` map and
                # allocates its own bare instance.
                child_orderset._run_permission_checks(
                    child_input,
                    request,
                    _fired=_fired,
                )
            # Per-branch permission gate on the parent -- fires e.g.
            # ``check_shelf_permission`` when the ``shelf`` branch is
            # active. Child orderset's own field gates fire via the
            # recursive call above. Deduped against the parent's
            # per-class set.
            cls._invoke_permission_method(bare, field_name, request, fired=class_fired)

    def check_permissions(self, request: Any) -> None:
        """Backward-compatible thin delegate to ``_run_permission_checks``.

        Cookbook callers reach for the bound-method form (cookbook
        ``orderset.py::AdvancedOrderSet.check_permissions``). The
        active-input normalization happens inside
        ``_run_permission_checks`` so both entry points share one source
        of truth. Routes through ``type(self)._run_permission_checks``
        against the input value parked on the instance
        (``self._input_value``); falls back to the empty list when no
        input has been parked.
        """
        type(self)._run_permission_checks(getattr(self, "_input_value", None), request)

    @classmethod
    def get_flat_orders(
        cls,
        order_data: list[tuple[str, Ordering | None]],
        prefix: str = "",
    ) -> list[tuple[str, Ordering | None]]:
        """Walk normalized order data into flat ``(field_path, direction)`` tuples.

        Port of
        ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_flat_orders``
        (cookbook lines 115-170) with two adaptations:

        - cookbook's DISTINCT ON tuple-half dropped (spec-028 Decision 12
          -- DISTINCT ON deferred to ``0.0.9``).
        - return shape changed from ``list[str]`` (cookbook's
          ``"-name"`` bare-string form) to
          ``list[tuple[str, Ordering | None]]`` (Spec Decision 5's
          ``OrderBy``-via-``Ordering.resolve`` discipline).

        ``prefix`` exists for cookbook-shape symmetry: callers who pass
        pre-walked normalized data (the output of
        ``normalize_input_value``) get a pass-through that re-applies
        the prefix per element. Slice 2's apply pipeline calls
        ``cls._normalize_input(input_value)`` first and then
        ``cls.get_flat_orders(data)`` against the normalized data, so
        ``prefix`` is empty in the common path. Future callers that
        walk a partially-prefixed subtree can pass an explicit prefix
        (e.g., ``"shelf__"``) and the helper concatenates it.
        """
        result: list[tuple[str, Ordering | None]] = []
        for field_path, direction in order_data:
            result.append((f"{prefix}{field_path}", direction))
        return result

    @classmethod
    def apply_sync(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Sync resolver entry point per spec-028 Decision 8.

        Steps:

        1. Resolve the request via ``_request_from_info``.
        2. Run per-field / per-branch permission checks BEFORE any
           ``order_by(...)`` clause touches the queryset (Spec Decision
           8 step 6 -- denial gates raise pre-mutation).
        3. Normalize the input into a flat
           ``[(field_path, Ordering | None), ...]`` list.
        4. Convert each ``(field_path, direction)`` pair into a Django
           ``OrderBy`` expression via ``direction.resolve(field_path)``;
           ``None`` directions are filtered (Spec Decision 13 -- null-
           direction edge case).
        5. Return ``queryset.order_by(*expressions)`` when at least one
           expression survived; otherwise return ``queryset`` unchanged.
        """
        request = cls._request_from_info(info)
        cls._run_permission_checks(input_value, request)
        data = cls._normalize_input(input_value)
        if not data:
            return queryset
        flat_orders = cls.get_flat_orders(data)
        expressions = [
            direction.resolve(field_path)
            for field_path, direction in flat_orders
            if direction is not None
        ]
        if not expressions:
            return queryset
        return queryset.order_by(*expressions)

    @classmethod
    async def apply_async(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Async sibling of ``apply_sync`` per spec-028 Decision 8 sync/async-split.

        Wraps ``_run_permission_checks`` in
        ``sync_to_async(thread_sensitive=True)`` so a consumer's
        ``check_*_permission`` hook that performs a blocking ORM read
        does not block the event loop. ``get_flat_orders`` and
        ``queryset.order_by(...)`` are NOT wrapped -- they are
        pure-Python parsing + a queryset-method call that does no I/O
        (per spec-028 Decision 8 step 7 + N7 of rev1).

        The order side has NO equivalent of the filter side's
        ``_derive_related_visibility_querysets_async`` /
        ``_collect_nested_visibility_querysets_async`` work because
        ordering does not re-derive child querysets per branch -- the
        flat ``order_by`` clause already references the relation paths
        directly via Django's ORM walker.
        """
        from asgiref.sync import sync_to_async

        request = cls._request_from_info(info)
        await sync_to_async(cls._run_permission_checks, thread_sensitive=True)(
            input_value,
            request,
        )
        data = cls._normalize_input(input_value)
        if not data:
            return queryset
        flat_orders = cls.get_flat_orders(data)
        expressions = [
            direction.resolve(field_path)
            for field_path, direction in flat_orders
            if direction is not None
        ]
        if not expressions:
            return queryset
        return queryset.order_by(*expressions)
