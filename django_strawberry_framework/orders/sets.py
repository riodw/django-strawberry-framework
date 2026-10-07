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
  ``_active_permission_targets`` / ``_invoke_permission_method`` /
  ``_request_from_info``) that drives
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
from collections.abc import Callable, Generator, Iterable
from contextvars import ContextVar
from typing import TYPE_CHECKING, ClassVar, TypeVar, cast

from django.db import models
from django.db.models.constants import LOOKUP_SEP
from strawberry import UNSET
from typing_extensions import override

from ..exceptions import ConfigurationError, PathResolutionError, _safe_arg_repr, _safe_type_name
from ..optimizer.predicates import visible_row_exists, visible_value
from ..sets_mixins import (
    ActiveInputPermissionAttrs,
    ActiveInputPermissionMixin,
    ClassBasedTypeNameMixin,
    SetLifecycleAttrs,
    collect_related_declarations,
    expanded_once,
    reject_captured_branches,
    require_re_readable_field_declaration,
    should_cache_expansion,
)
from ..utils.input_values import SetInputTraversal
from ..utils.inputs import promote_set_meta_fields, read_set_meta_fields
from ..utils.permissions import set_bound_type, walk_declared_relation_path
from ..utils.querysets import (
    apply_type_visibility_async,
    apply_type_visibility_sync,
    base_queryset,
    model_for,
    relation_target_type,
    run_in_one_sync_boundary,
)
from ..utils.relations import (
    classify_path,
    leading_relation_hops,
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

if TYPE_CHECKING:
    from collections.abc import Collection

    from django.db.models.expressions import OrderBy
    from typing_extensions import TypeIs

    from ..types.base import DjangoType
    from ..types.definition import DjangoTypeDefinition

_NormalizedTerms = tuple[tuple[str, "Ordering | None"], ...]
_M = TypeVar("_M", bound=models.Model)
#: The rows a scoping ``DjangoType``'s ``get_queryset`` lets one request see, per type.
_VisibleRows = Callable[["type[DjangoType]"], "models.QuerySet[models.Model]"]

#: Recourse for an async-only ``get_queryset`` behind a related order term on ``apply_sync``.
_ORDER_ASYNC_RECOURSE = (
    "A related order term reads its target type's get_queryset; await "
    "OrderSet.apply_async from an async resolver instead, or redefine get_queryset "
    "as a sync method."
)


@dataclasses.dataclass(frozen=True, slots=True)
class _AppliedNormalization:
    """One immutable attestation that a public ``apply_*`` normalized an input.

    ``orderset_class`` and ``input_value`` identify WHICH application this
    attests to (both compared by identity, never by equality - a consumer
    ``__eq__`` has no say in whether an attestation applies); ``terms`` is the
    already-validated tuple of primitives that application ordered by.
    """

    orderset_class: type[OrderSet]
    input_value: object
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

    Closure is TERMINAL. A descendant created while the scope was live keeps
    this object through the context it copied, and it may resume after the
    owning resolution has ended; the closed flag makes every later publication
    and every later claim inert, so the ledger cannot regain invocation state
    -- or hold an input object alive -- past the resolution it belongs to.
    """

    __slots__ = (
        "_claimed",
        "_closed",
        "_lock",
        "_records",
    )

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: list[_AppliedNormalization] = []
        self._claimed: list[tuple[type[OrderSet], object]] = []
        self._closed = False

    def publish(self, record: _AppliedNormalization) -> None:
        """Append one attestation. Never replaces or removes another.

        A publication after closure is dropped, which is exactly what a public
        ``apply_*`` outside any scope already does.
        """
        with self._lock:
            if self._closed:
                return
            self._records.append(record)

    def claim(
        self,
        orderset_class: type[OrderSet],
        input_value: object,
    ) -> _NormalizedTerms | None:
        """Claim the terms attested for this exact class and input object.

        Returns ``None`` when nothing applicable was published, when this pair
        was already claimed in this resolution, or when the ledger is closed.
        Raises when two applicable attestations disagree.
        """
        with self._lock:
            if self._closed:
                return None
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
        """Mark the ledger terminal and drop every attestation and claim.

        The scope resets its binding on both exits, but a child task or worker
        thread may still hold this object through a context it copied earlier.
        Emptying alone would let such a descendant repopulate the object and
        claim from it after the resolution ended, so the tombstone and the two
        clears are set under ONE lock acquisition: a descendant either observes
        the open ledger in full or the closed one, never a half-cleared one.
        """
        with self._lock:
            self._closed = True
            self._records.clear()
            self._claimed.clear()


_ORDER_NORMALIZATION_CAPTURE: ContextVar[_NormalizationLedger | None] = ContextVar(
    "django_strawberry_framework_order_normalization_capture",
    default=None,
)


@contextlib.contextmanager
def capture_applied_order_normalization() -> Generator[None, None, None]:
    """Open the invocation-scoped ledger public ``apply_*`` attests into.

    The list field wraps public ordering and its offset guard in one scope so
    the guard can reuse the terms the ``OrderSet`` already validated, instead of
    normalizing the client input a second time. The scope is a ``ContextVar``,
    never ``info.context``: a public ``OrderSet.apply_*`` call on a connection or
    in a hand-written resolver runs outside any scope and leaves no state
    anywhere, the consumer's context object is never written or cleared, and a
    concurrent resolution that opened its own scope has its own ledger.

    The ledger is CLOSED and the binding reset in ``finally``, so neither a
    rejected request nor a child task that outlived the resolution can carry a
    record into the next one. Closure runs first and the reset runs in its own
    ``finally``: a descendant holding the copied context observes the tombstone
    the moment the scope ends, and a failing reset still cannot leave the
    ledger open.

    The scope yields nothing: the ledger is reached only through the
    ``ContextVar``, so no caller can retain a handle to it by taking the
    context manager's value.
    """
    ledger = _NormalizationLedger()
    token = _ORDER_NORMALIZATION_CAPTURE.set(ledger)
    try:
        yield
    finally:
        try:
            ledger.close()
        finally:
            _ORDER_NORMALIZATION_CAPTURE.reset(token)


def _record_applied_normalization(
    cls: type[OrderSet],
    input_value: object,
    data: list[tuple[str, Ordering | None]],
) -> None:
    """Attest one successful normalization into the active ledger, if any.

    Appends; it can never displace another application's attestation, so a
    delegating override that applies in a child task publishes to the ledger
    its parent will claim from, while an unrelated application in that same
    child appends under its own identity and is never claimed. A descendant
    that outlives the resolution reaches a CLOSED ledger, whose publish is
    inert - identical to applying outside any scope at all.
    """
    ledger = _ORDER_NORMALIZATION_CAPTURE.get()
    if ledger is not None:
        ledger.publish(_AppliedNormalization(cls, input_value, tuple(data)))


def _is_normalized_term(term: object) -> TypeIs[tuple[str, Ordering | None]]:
    """Return whether ``term`` is an EXACT ``(str, Ordering | None)`` 2-tuple.

    Exact-type checks only, so no consumer ``__len__`` / ``__getitem__`` /
    ``__eq__`` fires while the term is inspected.
    """
    if type(term) is not tuple:
        return False
    members: tuple[object, ...] = term
    return (
        len(members) == 2
        and type(members[0]) is str
        and (members[1] is None or type(members[1]) is Ordering)
    )


def _validate_normalized_terms(
    cls: type[OrderSet],
    data: object,
) -> list[tuple[str, Ordering | None]]:
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
    terms: list[object] = data
    for term in terms:
        if not _is_normalized_term(term):
            raise ConfigurationError(
                f"OrderSet {cls.__qualname__}._normalize_input returned invalid term "
                f"{_safe_arg_repr(term)}; expected a (field_path: str, direction: Ordering | None) tuple.",
            )
    # Every term passed ``_is_normalized_term`` above; no checker carries a
    # per-element narrowing back onto the list.
    return cast("list[tuple[str, Ordering | None]]", terms)


def _order_paths(orderset: type[object]) -> Iterable[str]:
    """Return the ``Meta.fields`` paths a target order set exposes (its branches are walked apart)."""
    # ``reject_captured_branches`` hands back a ``RelatedOrder`` target, an ``OrderSet``.
    return cast("type[OrderSet]", orderset)._expand_meta_fields().keys()


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
        bases: tuple[type[object], ...],
        attrs: dict[str, object],
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

    # The name-keyed ``RelatedOrder`` declarations ``OrderSetMetaclass`` stores on every
    # class it builds (``sets_mixins.py::collect_related_declarations``, an ``OrderedDict``).
    # Annotation only: the metaclass is the one writer.
    related_orders: ClassVar[dict[str, RelatedOrder]]

    # Cache for fully-resolved fields per Layer 4 of spec-028 Decision 3.
    _expanded_fields: ClassVar[OrderedDict[str, RelatedOrder | None] | None] = None
    # Expansion reentry-guard slot (named by ``_lifecycle.guard``):
    # ``sets_mixins.expanded_once`` sets it around ``get_fields``'s build and
    # clears it in a ``finally``. No reentry branch reads it, because the
    # build never re-enters ``get_fields`` -- ``_expand_meta_fields`` expands
    # this class's own ``Meta.fields`` and never calls ``get_fields`` on a
    # ``RelatedOrder`` target -- so the order side passes no ``on_reentry``.
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
    def get_fields(cls) -> OrderedDict[str, RelatedOrder | None]:
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

        def _build() -> OrderedDict[str, RelatedOrder | None]:
            fields = cls._expand_meta_fields()
            for k, v in cls.related_orders.items():
                fields[k] = v
            reject_captured_branches(
                cls,
                cls.related_orders,
                related_attr="related_orders",
                target_attr="orderset",
                reached_paths=_order_paths,
            )

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
    def _expand_meta_fields(cls) -> OrderedDict[str, RelatedOrder | None]:
        """Expand ``Meta.fields`` into an ``OrderedDict`` keyed by field name.

        Supports list / tuple form (``["title", "subtitle"]``) and the
        ``"__all__"`` shorthand (every column-backed model field name
        per spec-028 -- forward FK columns are included,
        M2M managers and reverse FKs are excluded). Unordered ``set`` /
        ``frozenset`` declarations expand in one ``repr``-sorted order under
        every ``PYTHONHASHSEED`` (``read_set_meta_fields``); dict-shaped
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
        fields: OrderedDict[str, RelatedOrder | None] = OrderedDict()
        meta = getattr(cls, "Meta", None)
        # Shared reader: synonym resolve + unordered ``set`` / ``frozenset``
        # canonicalization. No write-back here -- the
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
        # ``require_re_readable_field_declaration`` refused anything but a collection.
        for field_path in cast("Collection[object]", meta_fields):
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
    def _input_has_active_terms(cls, input_value: object) -> bool:
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
    def _normalize_input(cls, input_value: object) -> list[tuple[str, Ordering | None]]:
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
    @override
    def _prepare_permission_input(cls, _input_value: object) -> None:
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
    def _active_order_terms(
        cls,
        flat_orders: list[tuple[str, Ordering | None]],
        *,
        model: type[models.Model],
    ) -> list[tuple[int, str, Ordering]]:
        """Return ``(index, field_path, direction)`` for every term with a direction, validated.

        A ``None`` direction contributes no term. A direction that is not an
        ``Ordering`` member, and a path ``classify_path`` cannot resolve against
        ``model``, raise ``ConfigurationError`` naming the term.
        """
        terms: list[tuple[int, str, Ordering]] = []
        for index, (field_path, direction) in enumerate(flat_orders):
            if direction is None:
                continue
            # basedpyright: trust boundary: a consumer ``get_flat_orders`` override can return any
            # direction
            if not isinstance(direction, Ordering):  # pyright: ignore[reportUnnecessaryIsInstance]
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
            terms.append((index, field_path, direction))
        return terms

    @classmethod
    def _scoped_hops(
        cls,
        model: type[models.Model],
        field_path: str,
    ) -> tuple[tuple[str, type[DjangoType]], ...]:
        """Return ``(joined path, scoping type)`` per relation ``field_path`` crosses that hides rows.

        The relations are ``utils/relations.py::leading_relation_hops``'s over
        ``model``, each reaching the model Django's join reaches; a ``pk`` segment
        on a model keyed by a relation is that relation, named by its field. Each
        answers for one ``DjangoType``: a relation a ``RelatedOrder`` declares
        (``utils/permissions.py::walk_declared_relation_path``) for the type its
        target set is bound to, any other relation, the intermediate models of a
        declaration whose ``field_name`` spans several relations included, for
        ``utils/querysets.py::relation_target_type``'s type, a path re-entering
        the model of the set it walks from reading the type that set is bound
        to. A relation whose type keeps the identity ``get_queryset``, or whose
        model no type registers, hides nothing and is left out, so a path
        crossing only such relations orders by its plain column.
        """
        joins = leading_relation_hops(model, field_path)
        if not joins:
            return ()
        declared, _remainder = walk_declared_relation_path(
            cls,
            field_path,
            related_attr=cls._permission.traversal.related_attr,
            target_attr=cls._permission.target_attr,
        )
        # The set each join is walked from (its re-entry root) and, for the join a
        # declaration ends on, the type that declaration's target set is bound to.
        root = set_bound_type(cls)
        roots: dict[int, type[DjangoType] | None] = {}
        owners: dict[int, type[DjangoType] | None] = {}
        start = 0
        for hop in declared:
            relation: object = getattr(hop.related_obj, "field_name", None) or hop.declared_attr
            end = start + len(str(relation).split(LOOKUP_SEP))
            roots.update(dict.fromkeys(range(start, end), root))
            root = None if hop.target is None else set_bound_type(hop.target)
            owners[end - 1] = root
            start = end
        types = [
            owners.get(position)
            or relation_target_type(join.target_model, root=roots.get(position, root))
            for position, join in enumerate(joins)
        ]
        segments = field_path.split(LOOKUP_SEP)
        reached = model
        joined: list[str] = []
        scoped: list[tuple[str, type[DjangoType]]] = []
        for segment, join, target_type in zip(segments, joins, types, strict=False):
            joined.append(reached._meta.pk.name if segment == "pk" else segment)
            reached = join.target_model
            if target_type is not None and target_type.has_custom_get_queryset():
                scoped.append((LOOKUP_SEP.join(joined), target_type))
        return tuple(scoped)

    @classmethod
    def _resolve_order_expressions(
        cls,
        flat_orders: list[tuple[str, Ordering | None]],
        *,
        model: type[models.Model],
        visible_rows: _VisibleRows,
    ) -> tuple[dict[str, models.Aggregate], list[OrderBy]]:
        """Build ``(annotations, order_expressions)`` from flat ``(path, direction)`` pairs.

        A term reads only related rows the request may see. Each relation the
        path crosses whose type hides rows (``_scoped_hops``) contributes one
        ``optimizer/predicates.py::visible_row_exists`` test over that type's
        rows (``visible_rows``), correlated to the row the term's own join
        reaches; the term's value is ``optimizer/predicates.py::visible_value``,
        ``NULL`` wherever a test fails, so a hidden related row orders the parent
        exactly as a missing one does. A path crossing no such relation orders
        by its plain column.

        A term whose ``field_path`` traverses a **to-many** relation (reverse FK
        or M2M -- ``_path_traverses_to_many``) is ordered by an AGGREGATE of that
        value rather than the raw fan-out path: ``Min`` for an ascending
        direction, ``Max`` for a descending one, applied through an
        ``.annotate(<alias>=Min/Max(...))`` and then ordered by ``<alias>``. A
        raw ``order_by("rel__col")`` across a to-many relation adds a JOIN that
        multiplies parent rows (one per matching child), which silently
        duplicates / skips nodes under the connection's positional cursors and
        inflates ``totalCount``; the aggregate keeps exactly one row per parent
        (the annotation forces a GROUP BY on the parent), so cursors index
        distinct nodes and ``.count()`` counts distinct parents
        (``spec-030-connection_field-0_0_9`` P1-B). A hidden child's value is
        ``NULL`` inside the aggregate, which ``Min`` / ``Max`` skip, so a parent
        whose related rows are all hidden sorts like a parent with none. Scalar
        columns and to-one relation paths (forward FK / O2O, reverse O2O --
        which never multiply) are ordered directly, unchanged.

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
        annotations: dict[str, models.Aggregate] = {}
        expressions: list[OrderBy] = []
        for index, field_path, direction in cls._active_order_terms(flat_orders, model=model):
            tests = [
                visible_row_exists(visible_rows(scope), joined)
                for joined, scope in cls._scoped_hops(model, field_path)
            ]
            value = visible_value(field_path, tests) if tests else field_path
            if _path_traverses_to_many(model, field_path):
                # ``flatten_lookup_path``: LOOKUP_SEP must never survive into a
                # generated alias (one owner for the mangle).
                alias = f"_dst_order_{index}_{flatten_lookup_path(field_path)}"
                # Ascending vs descending: ``Ordering.is_ascending`` (same rule
                # ``Ordering.resolve`` uses) picks Min / Max for the aggregate.
                aggregate = models.Min if direction.is_ascending else models.Max
                annotations[alias] = aggregate(value)
                expressions.append(direction.resolve(alias))
            else:
                expressions.append(direction.resolve(value))
        return annotations, expressions

    @classmethod
    def _visible_rows_sync(cls, queryset: models.QuerySet[_M], info: object) -> _VisibleRows:
        """Return a reader of each scoping type's visible rows, derived on first use.

        A type's rows are its ``get_queryset`` over that type's model on
        ``queryset``'s database alias (``apply_type_visibility_sync``, which raises
        ``SyncMisuseError`` for an async-only hook), derived once per call.
        """
        derived: dict[type[DjangoType], models.QuerySet[models.Model]] = {}

        def rows(scope: type[DjangoType]) -> models.QuerySet[models.Model]:
            found = derived.get(scope)
            if found is None:
                seed = base_queryset(model_for(scope), using=queryset.db)
                found = derived[scope] = apply_type_visibility_sync(
                    scope,
                    seed,
                    info,
                    async_recourse=_ORDER_ASYNC_RECOURSE,
                )
            return found

        return rows

    @classmethod
    async def _visible_rows_async(
        cls,
        flat_orders: list[tuple[str, Ordering | None]],
        queryset: models.QuerySet[_M],
        info: object,
    ) -> _VisibleRows:
        """Await every scoping type's visible rows the active terms read, before the sync tail.

        ``_visible_rows_sync``'s rows, derived up front with
        ``apply_type_visibility_async`` so an async-only ``get_queryset`` works:
        the order expressions are built synchronously and read only this map.
        """
        derived: dict[type[DjangoType], models.QuerySet[models.Model]] = {}
        for _index, field_path, _direction in cls._active_order_terms(
            flat_orders,
            model=queryset.model,
        ):
            for _joined, scope in cls._scoped_hops(queryset.model, field_path):
                if scope not in derived:
                    seed = base_queryset(model_for(scope), using=queryset.db)
                    derived[scope] = await apply_type_visibility_async(scope, seed, info)
        return derived.__getitem__

    @classmethod
    def _prepared_orderings(
        cls,
        input_value: object,
    ) -> tuple[list[tuple[str, Ordering | None]], list[tuple[str, Ordering | None]]]:
        """Return ``(normalized terms, flat orders)`` for ``input_value``; flat orders empty when no term."""
        data = _validate_normalized_terms(cls, cls._normalize_input(input_value))
        return data, (cls.get_flat_orders(data) if data else [])

    @classmethod
    def _apply_orderings(
        cls,
        input_value: object,
        queryset: models.QuerySet[_M],
        prepared: tuple[list[tuple[str, Ordering | None]], list[tuple[str, Ordering | None]]],
        visible_rows: _VisibleRows,
    ) -> models.QuerySet[_M]:
        """Apply the prepared orderings to ``queryset`` - the un-colored tail.

        The shared body behind ``apply_sync`` / ``apply_async`` (the order-side
        mirror of the filter side's ``_apply_common_prelude`` /
        ``_apply_common_finalize`` split): ``prepared`` is
        ``_prepared_orderings``'s normalized input and flat orders, and
        ``visible_rows`` reads each scoping type's rows (``_visible_rows_sync``,
        or ``_visible_rows_async``'s awaited map). Empty-out ->
        ``_resolve_order_expressions`` (``None`` directions filtered; hidden
        related rows read as missing; to-many paths ordered via the
        row-preserving ``Min`` / ``Max`` aggregate annotation) -> conditional
        ``annotate(**annotations)`` -> ``order_by(*expressions)``; a term-less
        input returns ``queryset`` unchanged. Omitted fields and explicit
        GraphQL ``null`` directions both produce no term, preserving any
        pre-existing queryset order. Pure Python parsing + queryset-method calls
        that do no I/O, so the sync and async colorings differ ONLY in the
        permission-check and visibility colorings they run before this.
        """
        data, flat_orders = prepared
        if not data:
            _record_applied_normalization(cls, input_value, data)
            return queryset
        annotations, expressions = cls._resolve_order_expressions(
            flat_orders,
            model=queryset.model,
            visible_rows=visible_rows,
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
        input_value: object,
        queryset: models.QuerySet[_M],
        info: object,
    ) -> models.QuerySet[_M]:
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
           scalar / to-one paths order directly via ``direction.resolve``,
           while a to-many path orders by an aggregate annotation
           (``Min`` / ``Max``) so the parent row is not multiplied
           (``spec-030-connection_field-0_0_9`` P1-B); a related row a scoping
           type hides reads as missing (``_visible_rows_sync`` derives each
           such type's rows); ``None`` directions are filtered (spec-028
           Decision 13 -- null-direction edge case).
        5. ``annotate(**annotations)`` (when any to-many term produced one) then
           ``order_by(*expressions)`` when at least one expression survived;
           otherwise return ``queryset`` unchanged.
        """
        request = cls._request_from_info(info)
        cls._run_permission_checks(input_value, request)
        prepared = cls._prepared_orderings(input_value)
        return cls._apply_orderings(
            input_value,
            queryset,
            prepared,
            cls._visible_rows_sync(queryset, info),
        )

    @classmethod
    async def apply_async(
        cls,
        input_value: object,
        queryset: models.QuerySet[_M],
        info: object,
    ) -> models.QuerySet[_M]:
        """Async sibling of ``apply_sync`` per spec-028 Decision 8 sync/async-split.

        Wraps ``_run_permission_checks`` in ``run_in_one_sync_boundary``
        so a consumer's ``check_*_permission`` hook that performs a
        blocking ORM read does not block the event loop.
        It then awaits the visible rows of every type scoping a relation
        the active terms cross (``_visible_rows_async``), so an async-only
        target ``get_queryset`` works. ``get_flat_orders`` and
        ``queryset.order_by(...)`` are NOT wrapped -- they are pure-Python
        parsing + a queryset-method call that does no I/O (per spec-028
        Decision 8 step 7).
        """
        request = cls._request_from_info(info)
        await run_in_one_sync_boundary(cls._run_permission_checks, input_value, request)
        prepared = cls._prepared_orderings(input_value)
        visible_rows = await cls._visible_rows_async(prepared[1], queryset, info)
        return cls._apply_orderings(input_value, queryset, prepared, visible_rows)
