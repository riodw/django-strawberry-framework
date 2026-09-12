"""``OrderSet`` + ``OrderSetMetaclass`` - declaration, validation, and the apply pipeline.

The metaclass is a verbatim port of
``django_graphene_filters/orderset.py::OrderSetMetaclass``; ``OrderSet``
mixes the cookbook's cycle-safe ``get_fields`` (the Layer-4 expansion)
over ``ClassBasedTypeNameMixin`` from ``..sets_mixins``.

On top of that skeleton the module carries:

- The ``"__all__"`` expansion via the
  ``_get_concrete_field_names_for_order`` walk per spec-028.
- The resolver-facing classmethod pair ``apply_sync`` /
  ``apply_async`` (no ``apply(...)`` dispatcher per spec-028 DoD 4(c)).
- The classmethod permission pipeline, inherited from
  ``ActiveInputPermissionMixin`` (``_run_permission_checks`` /
  ``_active_permission_targets`` / ``_active_permission_field_paths`` /
  ``_invoke_permission_method`` / ``_request_from_info``) that drives
  active-input-only per-field ``check_<field>_permission`` dispatch per
  spec-028 Decision 8 step 6.
- The cookbook-style ``get_flat_orders`` classmethod walking the
  normalized data structure.
"""

from __future__ import annotations

import contextlib
import dataclasses
import threading
from collections import OrderedDict
from collections.abc import Iterator
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, ClassVar

from django.db import models
from strawberry import UNSET

from ..exceptions import ConfigurationError, PathResolutionError, _safe_arg_repr, _safe_type_name
from ..sets_mixins import (
    ActiveInputPermissionAttrs,
    ActiveInputPermissionMixin,
    ClassBasedTypeNameMixin,
    SetLifecycleAttrs,
    collect_related_declarations,
    expanded_once,
    require_re_readable_field_declaration,
    should_cache_expansion,
)
from ..utils.input_values import SetInputTraversal
from ..utils.inputs import promote_set_meta_fields, read_set_meta_fields
from ..utils.querysets import run_in_one_sync_boundary
from ..utils.relations import (
    classify_path,
)
from ..utils.relations import (
    path_traverses_to_many as _path_traverses_to_many,
)
from ..utils.strings import flatten_lookup_path
from .base import RelatedOrder
from .inputs import (
    Ordering,
    _ensure_field_specs,
    _field_specs,
    _get_concrete_field_names_for_order,
    normalize_input_value,
)

if TYPE_CHECKING:  # pragma: no cover - type-checking-only import.
    from ..types.definition import DjangoTypeDefinition

_NormalizedTerms = tuple[tuple[str, "Ordering | None"], ...]


@dataclasses.dataclass(frozen=True, slots=True)
class _AppliedNormalization:
    """One immutable attestation that a public ``apply_*`` normalized an input.

    ``orderset_class`` and ``input_value`` identify WHICH application this
    attests to (both compared by identity, never by equality - a consumer
    ``__eq__`` has no say in whether an attestation applies); ``terms`` is the
    already-validated tuple of primitives that application ordered by.
    """

    orderset_class: type
    input_value: Any
    terms: _NormalizedTerms


class _NormalizationLedger:
    """One list-field resolution's append-only record of applied normalizations.

    The transport between the public ``OrderSet.apply_*`` that ordered the
    queryset and the offset guard that must know which terms it ordered by. It
    is an append-only LEDGER rather than a slot because the two requirements
    pull in opposite directions: the guard has to receive an application that
    happened in a child task, a copied context, or a ``sync_to_async`` worker
    thread, while an unrelated application in any of those must not be able to
    displace the one the guard is waiting for. A slot can satisfy only one of
    those at a time - a shared mutable one loses the parent's record to the
    last writer, and a rebinding-only one loses a legitimate child's record to
    context isolation.

    So: every application appends, nothing ever overwrites, and the guard
    CLAIMS only the entries whose class and input object are the ones it asked
    about. A nested ``OrderSet`` applied between publication and check appends
    under its own identity and is simply not claimed. Claiming is
    once-per-(class, input): a second check in the same resolution finds the
    pair already claimed and falls back to two independent normalizations,
    which keeps an attestation standing for exactly the one application it
    describes.

    Entries whose class and input match but whose terms DISAGREE are a
    ``_normalize_input`` that answered differently for the same input within
    one resolution; the claim fails closed rather than picking one.

    The lock is not decoration: ``asgiref``'s ``sync_to_async`` runs the
    wrapped callable in a worker thread carrying a COPY of this context, so two
    threads can genuinely reach one ledger.
    """

    __slots__ = ("_claimed", "_lock", "_records")

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: list[_AppliedNormalization] = []
        self._claimed: list[tuple[type, Any]] = []

    def publish(self, record: _AppliedNormalization) -> None:
        """Append one attestation. Never replaces or removes another."""
        with self._lock:
            self._records.append(record)

    def claim(self, orderset_class: type, input_value: Any) -> _NormalizedTerms | None:
        """Claim the terms attested for this exact class and input object.

        Returns ``None`` when nothing applicable was published, or when this
        pair was already claimed in this resolution. Raises when two applicable
        attestations disagree.
        """
        with self._lock:
            for claimed_class, claimed_input in self._claimed:
                if claimed_class is orderset_class and claimed_input is input_value:
                    return None
            matched = [
                record.terms
                for record in self._records
                if record.orderset_class is orderset_class and record.input_value is input_value
            ]
            if not matched:
                return None
            self._claimed.append((orderset_class, input_value))
        first = matched[0]
        for other in matched[1:]:
            if other != first:
                raise ConfigurationError(
                    f"{orderset_class.__name__}._normalize_input is not pure; two "
                    f"applications of the same input in one resolution returned different "
                    f"results ({_safe_arg_repr(list(first))} != {_safe_arg_repr(list(other))}).",
                )
        return first

    def close(self) -> None:
        """Drop every attestation and claim when the resolution ends.

        The scope resets its binding on both exits, but a child task or worker
        thread may still hold this object through a context it copied earlier;
        emptying it means no invocation state outlives the invocation.
        """
        with self._lock:
            self._records.clear()
            self._claimed.clear()


_ORDER_NORMALIZATION_CAPTURE: ContextVar[_NormalizationLedger | None] = ContextVar(
    "django_strawberry_framework_order_normalization_capture",
    default=None,
)


@contextlib.contextmanager
def capture_applied_order_normalization() -> Iterator[None]:
    """Open the invocation-scoped ledger public ``apply_*`` attests into.

    The list field wraps public ordering and its offset guard in one scope so
    the guard can reuse the terms the ``OrderSet`` already validated, instead of
    normalizing the client input a second time. The scope is a ``ContextVar``,
    never ``info.context``: a public ``OrderSet.apply_*`` call on a connection or
    in a hand-written resolver runs outside any scope and leaves no state
    anywhere, the consumer's context object is never written or cleared, and a
    concurrent resolution that opened its own scope has its own ledger.

    The binding is reset AND the ledger emptied in ``finally``, so neither a
    rejected request nor a child task that outlived the resolution can carry a
    record into the next one.

    The scope yields nothing: the ledger is reached only through the
    ``ContextVar``, so no caller can retain a handle to it by taking the
    context manager's value.
    """
    ledger = _NormalizationLedger()
    token = _ORDER_NORMALIZATION_CAPTURE.set(ledger)
    try:
        yield
    finally:
        _ORDER_NORMALIZATION_CAPTURE.reset(token)
        ledger.close()


def _record_applied_normalization(
    cls: type,
    input_value: Any,
    data: list[tuple[str, Ordering | None]],
) -> None:
    """Attest one successful normalization into the active ledger, if any.

    Appends; it can never displace another application's attestation, so a
    delegating override that applies in a child task publishes to the ledger
    its parent will claim from, while an unrelated application in that same
    child appends under its own identity and is never claimed.
    """
    ledger = _ORDER_NORMALIZATION_CAPTURE.get()
    if ledger is not None:
        ledger.publish(_AppliedNormalization(cls, input_value, tuple(data)))


def _validate_normalized_terms(cls: type, data: Any) -> list[tuple[str, Ordering | None]]:
    """Enforce the OrderSet._normalize_input return contract at the pipeline boundary.

    Guarantees that normalized order data is a list of 2-tuples of (field_path: str,
    direction: Ordering | None). Rejects non-conforming returns immediately with an
    actionable ConfigurationError naming _normalize_input. Every shape is pinned by
    EXACT type, not ``isinstance``: a ``list`` subclass would run consumer
    ``__iter__`` in this very loop, a ``tuple`` subclass consumer ``__len__`` /
    ``__getitem__``, and a ``str`` subclass consumer ``__eq__`` in the purity
    compare or ``__format__`` in ``get_flat_orders``. The outer container is
    rejected before it is iterated and a term before its members are read, so
    everything downstream operates on trusted primitives with deterministic
    equality and no consumer hook left to fire.
    """
    if type(data) is not list:
        raise ConfigurationError(
            f"OrderSet {cls.__qualname__}._normalize_input returned invalid data "
            f"{_safe_arg_repr(data)}; expected a list of (field_path, direction) tuples.",
        )
    for term in data:
        if (
            type(term) is not tuple
            or len(term) != 2
            or type(term[0]) is not str
            or (term[1] is not None and type(term[1]) is not Ordering)
        ):
            raise ConfigurationError(
                f"OrderSet {cls.__qualname__}._normalize_input returned invalid term "
                f"{_safe_arg_repr(term)}; expected a (field_path: str, direction: Ordering | None) tuple.",
            )
    return data


class OrderSetMetaclass(type):
    """Discover ``RelatedOrder`` declarations and bind them to the new class.

    Direct port of
    ``django_graphene_filters/orderset.py::OrderSetMetaclass``. Inherited
    ``related_orders`` are collected in MRO order with the current class's
    own declarations overriding same-named inherited ones (standard Python
    MRO semantics); every collected ``RelatedOrder`` is bound back to the
    new class via ``bind_orderset``. ``Meta.fields`` resolution is
    ``utils/inputs.py::promote_set_meta_fields`` (no cookbook synonym;
    shared write-back with ``FilterSetMetaclass``).
    """

    def __new__(
        cls: type[OrderSetMetaclass],
        name: str,
        bases: tuple,
        attrs: dict,
    ) -> OrderSetMetaclass:
        """Build the class, collect ``RelatedOrder`` declarations, bind owner."""
        # No cookbook ``order_fields`` synonym (``fields_alias=None``); the
        # call still goes through the shared write-back so FilterSet / OrderSet
        # class Meta cannot grow divergent field-fingerprint rules.
        promote_set_meta_fields(attrs.get("Meta"))
        new_class = super().__new__(cls, name, bases, attrs)

        # Collect the ``RelatedOrder`` declarations and bind each to the new
        # class via the shared set-family collector. The
        # plain ``type`` metaclass does no MRO merge, so
        # ``inherit_from_bases=True`` copies each base's ``related_orders``
        # first (reverse iteration lets earlier bases win) before the class
        # body's own ``attrs`` override - the behavior of
        # ``django_graphene_filters/orderset.py::OrderSetMetaclass.__new__``.
        collect_related_declarations(
            new_class,
            bases,
            own_items=attrs.items(),
            declaration_type=RelatedOrder,
            collection_attr="related_orders",
            inherit_from_bases=True,
        )
        return new_class


class OrderSet(ClassBasedTypeNameMixin, ActiveInputPermissionMixin, metaclass=OrderSetMetaclass):
    """Consumer-facing ``OrderSet`` foundation.

    Layer-3 + Layer-4 + resolver-API port of
    ``django_graphene_filters/orderset.py::AdvancedOrderSet``. Inherits
    ``type_name_for`` from ``ClassBasedTypeNameMixin`` (the shared
    ``{cls.__name__}InputType`` naming rule), the Decision-8 permission
    facade from ``ActiveInputPermissionMixin``, and its
    ``related_orders`` collection via ``OrderSetMetaclass``.

    The resolver-facing surface is the classmethod pair ``apply_sync`` /
    ``apply_async`` per spec-028 Decision 8 step 7. Each carries ``info``
    end-to-end so per-field ``check_<field>_permission`` gates and
    active-input-only scope run consistently. There is **no**
    ``apply(...)`` dispatcher (spec-028 DoD 4(c) -- the filter side's
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

    # Binding seam - populated by ``finalize_django_types`` phase 2.5 in
    # per spec-028 Decision 6. The slot's existence is the contract here;
    # the binding write lands with the field factory. Same shape as the
    # filter side's ``FilterSet._owner_definition``.
    _owner_definition: DjangoTypeDefinition | None = None

    # Cache for fully-resolved fields per Layer 4 of spec-028 Decision 3.
    _expanded_fields = None
    # Recursion guard around ``get_fields`` so a self-referential
    # ``RelatedOrder`` does not blow the stack. The slot stays in place
    # for future defensive use even though the expansion removes
    # the explicit reentry-branch test from ``_expand_meta_fields`` (per
    # the planning-pass disposition -- the branch was structurally
    # unreachable through the shipped surface).
    _is_expanding_fields = False

    # Family binding-state descriptor: the single source for the lifecycle attr
    # names ``get_fields`` (via ``expanded_once``) and ``registry.clear()`` (via
    # ``clear_order_input_namespace``'s ``binding_attrs``) reference, instead of
    # re-spelling the tuple.
    # Mirrors ``FilterSet._lifecycle`` with the order-side slot names.
    _lifecycle: ClassVar[SetLifecycleAttrs] = SetLifecycleAttrs(
        owner="_owner_definition",
        cache="_expanded_fields",
        guard="_is_expanding_fields",
    )

    # Family permission-facade config: shared with ``FilterSet`` through
    # ``ActiveInputPermissionMixin``. Order inputs are a top-level list with
    # ``UNSET`` / ``None`` for omitted fields, no operator-bag logic keys.
    _permission: ClassVar[ActiveInputPermissionAttrs] = ActiveInputPermissionAttrs(
        family_label="OrderSet",
        target_attr="orderset",
        traversal=SetInputTraversal(
            field_specs=_field_specs,
            related_attr="related_orders",
            unset_sentinel=UNSET,
            handle_top_level_list=True,
        ),
    )

    @classmethod
    def get_fields(cls) -> OrderedDict:
        """Return ``Meta.fields`` expansion merged with ``related_orders``.

        Direct port of
        ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields``
        with the same two-condition cache write
        gate the filter side uses at ``FilterSet.get_filters``:

        - ``cls.__dict__.get("_expanded_fields")`` is checked directly
          (NOT via ``getattr``) so a subclass does not inherit a parent's
          completed cache via MRO.
        - the cache is only written when ``related_orders`` is on this
          class's ``__dict__`` AND every ``_orderset`` is a real class
          (no unresolved string forward references remain).

        ``Meta.fields = "__all__"`` expands via
        ``_get_concrete_field_names_for_order``
        (spec-028 Decision 3).
        """

        def _build() -> OrderedDict:
            fields = cls._expand_meta_fields()
            for k, v in getattr(cls, "related_orders", {}).items():
                fields[k] = v

            # The two-condition cache-write gate (own ``related_orders`` +
            # no unresolved string lazy targets) is single-sited in
            # ``sets_mixins.should_cache_expansion``.
            if should_cache_expansion(
                cls,
                related_attr="related_orders",
                target_slot="_orderset",
            ):
                cls._expanded_fields = fields
            return fields

        # The class-level expansion cache + reentry-guard skeleton is shared with
        # ``FilterSet.get_filters`` through ``sets_mixins.expanded_once``.
        # The order side passes no ``on_reentry``: its
        # expansion never re-enters ``get_fields`` (the filter side's
        # self-referential-cycle fallback has no order analogue).
        return expanded_once(
            cls,
            cache_attr=cls._lifecycle.cache,
            guard_attr=cls._lifecycle.guard,
            build=_build,
        )

    @classmethod
    def _expand_meta_fields(cls) -> OrderedDict:
        """Expand ``Meta.fields`` into an ``OrderedDict`` keyed by field name.

        Supports list / tuple form (``["title", "subtitle"]``) and the
        ``"__all__"`` shorthand (every column-backed model field name
        per spec-028 -- forward FK columns are included,
        M2M managers and reverse FKs are excluded). Unordered ``set`` /
        ``frozenset`` declarations expand in the same ``repr``-sorted order
        Layer-6 factory kwargs hash (``read_set_meta_fields``); dict-shaped
        declarations iterate their keys (the django-filter lookup-bag shape
        degrades to its field names).

        Two declaration contracts are enforced at this gate:

        - ``meta_fields`` must be a RE-READABLE collection (any
          ``collections.abc.Collection`` that is not a text atom: list /
          tuple / set / frozenset / dict / dict view / ``range`` / a custom
          collection). The expansion re-runs whenever a lazy
          ``RelatedOrder`` target keeps the ``get_fields`` cache gate from
          writing, so a one-shot iterator would expand correctly once and
          then silently rebuild to an empty or partial field set.
        - Every entry is a field-name STRING, model or no model. A
          model-less related-only set defers path validation to the
          concrete ``queryset.model`` at apply time, but the entry type is
          checked here so a ``None`` / bytes / non-hashable entry raises the
          typed declaration error instead of silently landing in the
          expansion (or raising raw ``TypeError`` from the dict write).
        """
        fields: OrderedDict = OrderedDict()
        meta = getattr(cls, "Meta", None)
        # Shared reader with Layer-6 factory kwargs: synonym resolve + unordered
        # ``set`` / ``frozenset`` canonicalization. No write-back here -- the
        # metaclass owns alias promotion; expansion must not mutate class Meta.
        meta_fields = read_set_meta_fields(meta)
        if meta_fields is None:
            return fields
        if meta_fields == "__all__":
            # ``_get_concrete_field_names_for_order`` is imported at module
            # level with the other ``.inputs`` symbols; ``inputs.py`` only
            # TYPE_CHECKING-imports ``OrderSet``, so the runtime cycle stays
            # inert without a deferred local import.
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
        # Re-readability is a declaration contract shared with the filter
        # family, so the gate is theirs jointly
        # (``sets_mixins.py::require_re_readable_field_declaration``): this
        # expansion re-runs whenever a lazy ``RelatedOrder`` keeps the
        # two-condition cache gate in ``get_fields`` from writing, and a
        # one-shot declaration would expand correctly once and then silently
        # rebuild to an EMPTY or partial field set. Dict-shaped fields iterate
        # their keys (the django-filter lookup-bag shape degrades to its field
        # names).
        require_re_readable_field_declaration(
            cls,
            meta_fields,
            subject="OrderSet",
            accepted="'__all__' or a re-readable collection of field names",
        )
        model = getattr(meta, "model", None)
        for field_path in meta_fields:
            # Entry-TYPE validation is unconditional: a model-less related-only
            # set defers path validation to the concrete ``queryset.model`` at
            # apply time, but every entry is a path TOKEN here regardless, so a
            # non-string entry is a declaration error at this gate instead of a
            # silent ``{None: None}`` / ``{b'title': None}`` expansion (or a raw
            # ``TypeError: unhashable type`` from the ``fields[...]`` write
            # below) when ``Meta.model`` is absent.
            if type(field_path) is not str:
                raise ConfigurationError(
                    f"OrderSet {cls.__qualname__}.Meta.fields entries must be field-name "
                    f"strings; got {_safe_type_name(field_path)} "
                    f"({_safe_arg_repr(field_path)}).",
                )
            if model is not None:
                try:
                    classify_path(model, field_path)
                except PathResolutionError as exc:
                    raise ConfigurationError(
                        f"OrderSet {cls.__qualname__}.Meta.fields contains invalid "
                        f"order path {field_path!r} for model {_safe_type_name(model)}: {exc}",
                    ) from exc
            fields[field_path] = None
        return fields

    # ------------------------------------------------------------------
    # Resolver-facing API (spec-028 Decision 8)
    # ------------------------------------------------------------------

    @classmethod
    def _input_has_active_terms(cls, input_value: Any) -> bool:
        """Return True if input_value contains at least one non-null ordering direction.

        Checks purity against the normalization the ``OrderSet`` actually ordered
        by: the active :func:`capture_applied_order_normalization` ledger is
        asked for an attestation naming this class and this exact input object
        (two normalizations total, one in apply and one here). Where the ledger
        holds none - an override that never delegates to the base
        implementation, or a call outside any scope - the check falls back to
        two independent normalizations and compares those (three calls total).
        Attestations are claimed once per class-and-input pair, so a second
        check within one resolution also takes the two-normalization path rather
        than reusing an attestation for an application it does not describe.

        Because the ledger is append-only, an attestation published from a child
        task, a copied context, or a worker thread - the shapes a legitimate
        ``apply_async`` override delegating to ``super()`` produces - reaches
        this check, while an unrelated application in any of those appends under
        its own identity and is never claimed here.

        Any disagreement raises an actionable :class:`ConfigurationError` naming
        :meth:`_normalize_input`.
        """
        applied_data: _NormalizedTerms | None = None
        ledger = _ORDER_NORMALIZATION_CAPTURE.get()
        if ledger is not None:
            applied_data = ledger.claim(cls, input_value)

        data_check = _validate_normalized_terms(cls, cls._normalize_input(input_value))

        if applied_data is not None:
            if applied_data != tuple(data_check):
                first_repr = _safe_arg_repr(list(applied_data))
                raise ConfigurationError(
                    f"{cls.__name__}._normalize_input is not pure; returned different results "
                    f"for the same input ({first_repr} != {_safe_arg_repr(data_check)}).",
                )
            data_to_walk = list(applied_data)
        else:
            data_check2 = _validate_normalized_terms(cls, cls._normalize_input(input_value))
            if data_check != data_check2:
                raise ConfigurationError(
                    f"{cls.__name__}._normalize_input is not pure; returned different results "
                    f"for the same input ({_safe_arg_repr(data_check)} != {_safe_arg_repr(data_check2)}).",
                )
            data_to_walk = data_check

        flat_orders = cls.get_flat_orders(data_to_walk)
        return any(direction is not None for _, direction in flat_orders)

    @classmethod
    def _normalize_input(cls, input_value: Any) -> list[tuple[str, Ordering | None]]:
        """Normalize client order input into an internal term representation.

        Purity obligation:
            This method must be a pure, deterministic function of ``input_value``.
            An argument-bearing ``DjangoListField`` request normalizes the input once
            during public apply (``apply_sync`` or ``apply_async``) and once during the
            active-term check, which compares against the terms the base apply attested
            into the list field's invocation-scoped ledger - including when the apply
            ran in a child task or worker thread. An override that does not delegate to
            the base apply attests nothing, so the check performs two independent reads
            (three calls total). Any stateful or non-deterministic disagreement raises an
            actionable :class:`ConfigurationError` naming this method.
        """
        return normalize_input_value(cls, input_value)

    @classmethod
    def _prepare_permission_input(cls, _input_value: Any) -> None:
        """Initialize direct-call provenance before active permission traversal.

        The order family builds its field specs lazily, so a direct call can
        reach the shared facade before this class has any. Implemented as the
        mixin's family hook rather than an override so the facade itself stays
        single-sourced on ``ActiveInputPermissionMixin``.
        """
        _ensure_field_specs(cls, _input_value)

    @classmethod
    def get_flat_orders(
        cls,
        order_data: list[tuple[str, Ordering | None]],
        prefix: str = "",
    ) -> list[tuple[str, Ordering | None]]:
        """Walk normalized order data into flat ``(field_path, direction)`` tuples.

        Port of
        ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_flat_orders``
        with two adaptations:

        - cookbook's DISTINCT ON tuple-half dropped (spec-028 Decision 12
          -- no DISTINCT ON surface ships).
        - return shape changed from ``list[str]`` (cookbook's
          ``"-name"`` bare-string form) to
          ``list[tuple[str, Ordering | None]]`` (spec-028 Decision 5's
          ``OrderBy``-via-``Ordering.resolve`` discipline).

        ``prefix`` exists for cookbook-shape symmetry: callers who pass
        pre-walked normalized data (the output of
        ``normalize_input_value``) get a pass-through that re-applies
        the prefix per element. The apply pipeline calls
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
    def _resolve_order_expressions(
        cls,
        flat_orders: list[tuple[str, Ordering | None]],
        *,
        model: type[models.Model],
    ) -> tuple[dict[str, Any], list]:
        """Build ``(annotations, order_expressions)`` from flat ``(path, direction)`` pairs.

        A term whose ``field_path`` traverses a **to-many** relation (reverse FK
        or M2M -- ``_path_traverses_to_many``) is ordered by an AGGREGATE of the
        child column rather than the raw fan-out path: ``Min`` for an ascending
        direction, ``Max`` for a descending one, applied through an
        ``.annotate(<alias>=Min/Max(path))`` and then ordered by ``<alias>``. A
        raw ``order_by("rel__col")`` across a to-many relation adds a JOIN that
        multiplies parent rows (one per matching child), which silently
        duplicates / skips nodes under the connection's positional cursors and
        inflates ``totalCount``; the aggregate keeps exactly one row per parent
        (the annotation forces a GROUP BY on the parent), so cursors index
        distinct nodes and ``.count()`` counts distinct parents
        (``spec-030-connection_field-0_0_9`` P1-B). Scalar columns and to-one
        relation paths (forward FK / O2O, reverse O2O -- which never
        multiply) are ordered directly, unchanged.

        NULLS positioning carries onto the aggregate's ``OrderBy`` because the
        alias is resolved through the same ``Ordering.resolve``; mixed scalar +
        to-many terms in one ``orderBy`` annotate independently and compose.

        Connection pagination preserves this shape without stacking incompatible
        query layers. A root ``DjangoConnectionField`` applies this grouped
        queryset before its normal cursor slice. A synthesized nested relation
        connection carrying ``orderBy:`` is deliberately not window/lateral
        planned and runs the per-parent connection pipeline instead. Therefore a
        to-many aggregate order never sits below the optimizer's
        ``_dst_row_number`` window annotation; both SQLite and PostgreSQL execute
        the grouped root page or the unwindowed nested fallback directly.

        ``model`` is the concrete ``queryset.model`` supplied by
        ``_apply_orderings``. Order paths execute against that queryset, so its
        model is the only authoritative metadata root: ``Meta.model`` may be
        absent for a related-only set, or may name a base model while a valid
        direct caller applies the set to a concrete descendant carrying
        additional relations. Inferring from class/binding metadata makes
        correctness depend on declaration history and can miss a concrete
        to-many path, leaving the raw fan-out join this method exists to prevent.
        """
        annotations: dict[str, Any] = {}
        expressions: list = []
        for index, (field_path, direction) in enumerate(flat_orders):
            if direction is None:
                continue
            if not isinstance(direction, Ordering):
                raise ConfigurationError(
                    f"OrderSet {cls.__qualname__} received invalid order direction "
                    f"{_safe_arg_repr(direction)} for path {field_path!r}; "
                    f"expected an Ordering enum member.",
                )
            try:
                classify_path(model, field_path)
            except PathResolutionError as exc:
                raise ConfigurationError(
                    f"OrderSet {cls.__qualname__} received invalid order path "
                    f"{field_path!r} for model {_safe_type_name(model)}: {exc}",
                ) from exc
            if _path_traverses_to_many(model, field_path):
                # ``flatten_lookup_path``: LOOKUP_SEP must never survive into a
                # generated alias (one owner for the mangle).
                alias = f"_dst_order_{index}_{flatten_lookup_path(field_path)}"
                # Ascending vs descending: ``Ordering.is_ascending`` (same rule
                # ``Ordering.resolve`` uses) picks Min / Max for the aggregate.
                aggregate = models.Min if direction.is_ascending else models.Max
                annotations[alias] = aggregate(field_path)
                expressions.append(direction.resolve(alias))
            else:
                expressions.append(direction.resolve(field_path))
        return annotations, expressions

    @classmethod
    def _apply_orderings(cls, input_value: Any, queryset: models.QuerySet) -> models.QuerySet:
        """Apply the normalized orderings to ``queryset`` - the un-colored tail.

        The shared body behind ``apply_sync`` / ``apply_async`` (the order-side
        mirror of the filter side's ``_apply_common_prelude`` /
        ``_apply_common_finalize`` split): normalize the input -> empty-out ->
        ``get_flat_orders`` -> ``_resolve_order_expressions`` (``None``
        directions filtered; to-many paths ordered via the row-preserving
        ``Min`` / ``Max`` aggregate annotation) -> conditional
        ``annotate(**annotations)`` -> ``order_by(*expressions)``; a term-less
        input returns ``queryset`` unchanged. Omitted fields and explicit
        GraphQL ``null`` directions both produce no term, preserving any
        pre-existing queryset order. Pure Python parsing + queryset-method calls
        that do no I/O, so the sync and async colorings differ ONLY in the
        permission-check coloring they run before this.
        """
        data = _validate_normalized_terms(cls, cls._normalize_input(input_value))
        if not data:
            _record_applied_normalization(cls, input_value, data)
            return queryset
        flat_orders = cls.get_flat_orders(data)
        annotations, expressions = cls._resolve_order_expressions(
            flat_orders,
            model=queryset.model,
        )
        if not expressions:
            _record_applied_normalization(cls, input_value, data)
            return queryset
        if annotations:
            queryset = queryset.annotate(**annotations)
        queryset = queryset.order_by(*expressions)
        _record_applied_normalization(cls, input_value, data)
        return queryset

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
           ``order_by(...)`` clause touches the queryset
           (spec-028 Decision 8 step 6 -- denial gates raise pre-mutation).
        3. Normalize the input into a flat
           ``[(field_path, Ordering | None), ...]`` list.
        4. Convert each ``(field_path, direction)`` pair into a Django
           ``OrderBy`` expression via ``_resolve_order_expressions`` --
           scalar / to-one paths order directly via
           ``direction.resolve(field_path)``, while a to-many path orders by an
           aggregate annotation (``Min`` / ``Max``) so the parent row is not
           multiplied (``spec-030-connection_field-0_0_9`` P1-B); ``None``
           directions are filtered (spec-028 Decision 13 -- null-direction
           edge case).
        5. ``annotate(**annotations)`` (when any to-many term produced one) then
           ``order_by(*expressions)`` when at least one expression survived;
           otherwise return ``queryset`` unchanged.
        """
        request = cls._request_from_info(info)
        cls._run_permission_checks(input_value, request)
        return cls._apply_orderings(input_value, queryset)

    @classmethod
    async def apply_async(
        cls,
        input_value: Any,
        queryset: models.QuerySet,
        info: Any,
    ) -> models.QuerySet:
        """Async sibling of ``apply_sync`` per spec-028 Decision 8 sync/async-split.

        Wraps ``_run_permission_checks`` in ``run_in_one_sync_boundary``
        so a consumer's ``check_*_permission`` hook that performs a
        blocking ORM read does not block the event loop.
        ``get_flat_orders`` and ``queryset.order_by(...)`` are NOT
        wrapped -- they are pure-Python parsing + a queryset-method call
        that does no I/O (per spec-028 Decision 8 step 7).

        The order side has NO equivalent of the filter side's
        ``_derive_related_visibility_querysets_async`` /
        ``_collect_nested_visibility_querysets_async`` work because
        ordering does not re-derive child querysets per branch -- the
        flat ``order_by`` clause already references the relation paths
        directly via Django's ORM walker.
        """
        request = cls._request_from_info(info)
        await run_in_one_sync_boundary(cls._run_permission_checks, input_value, request)
        return cls._apply_orderings(input_value, queryset)
