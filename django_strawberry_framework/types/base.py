"""``DjangoType`` — Meta-class-driven Django-model-to-Strawberry-type adapter.

Consumer surface::

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = "__all__"

A nested ``Meta`` class declares the model and (optionally) ``fields``,
``exclude``, ``name``, and ``description``. Subclassing
triggers the ``__init_subclass__`` pipeline, which:

1. Detects whether the subclass declares its own ``Meta``. Intermediate
   abstract subclasses without ``Meta`` are skipped so consumers can
   layer their own bases on top of ``DjangoType``.
2. Validates ``Meta`` (required ``model``, ``fields``/``exclude``
   exclusivity, deferred-key rejection).
3. Synthesizes Strawberry annotations via ``converters.convert_scalar``
   and ``converters.convert_relation``.
4. Registers the resulting type with ``registry``.
5. Finalizes the class via ``@strawberry.type``.
"""

from typing import Any, ClassVar

import strawberry
from django.db import models

from ..exceptions import ConfigurationError
from ..optimizer.field_meta import FieldMeta
from ..optimizer.hints import OptimizerHint
from ..registry import registry
from ..utils.strings import snake_case
from .converters import convert_relation, convert_scalar
from .resolvers import _attach_relation_resolvers

# TODO(spec-foundation 0.0.4): introduce ``DjangoTypeDefinition`` (new
# module ``types/definition.py``) and ``PendingRelation`` (new module
# ``types/relations.py``) per ``docs/spec-foundation.md`` "Architecture
# (canonical, with pseudocode)". Imports land in step 1 of the phased
# implementation order; ``__init_subclass__`` consumes them in step 4.

DEFERRED_META_KEYS: frozenset[str] = frozenset(
    {
        "filterset_class",
        "orderset_class",
        "aggregate_class",
        "fields_class",
        "search_fields",
        # ``interfaces`` is in the deferred set rather than the allowed
        # set because the relay-interface application pass
        # (``cls.__bases__`` injection before ``strawberry.type``) has
        # not landed yet. Accepting the key without applying it would
        # silently produce types that look interface-bearing but are
        # not, which is exactly the alpha posture we want to avoid.
        "interfaces",
    },
)

ALLOWED_META_KEYS: frozenset[str] = frozenset(
    {
        "model",
        "fields",
        "exclude",
        "name",
        "description",
        "optimizer_hints",
    },
)


class DjangoType:
    """Base class for Django-model-backed Strawberry GraphQL types."""

    # TODO(spec-foundation 0.0.4): the canonical home for per-type
    # metadata moves to ``cls.__django_strawberry_definition__: DjangoTypeDefinition``.
    # The three ``ClassVar`` attributes below stay for one minor version
    # as a compat mirror so the optimizer walker's ``getattr(type_cls,
    # "_optimizer_field_map", None)`` / ``getattr(type_cls,
    # "_optimizer_hints", {})`` / ``cls._is_default_get_queryset`` reads
    # keep working without a same-slice walker rewrite. Mirrored as plain
    # class attributes (NOT ``@property``) per the verification report at
    # ``docs/spec-foundation.md`` "Should redo now". Removed in the next
    # minor once the walker reads through ``registry.get_definition(...)``.

    # Sentinel so ``has_custom_get_queryset`` can detect overrides.
    _is_default_get_queryset: ClassVar[bool] = True

    # Empty defaults so attribute reads on the base class (or on an
    # intermediate abstract subclass without ``Meta``) succeed without
    # ``AttributeError``.  ``__init_subclass__`` writes the populated
    # versions on every concrete subclass.
    _optimizer_field_map: ClassVar[dict[str, FieldMeta]] = {}
    _optimizer_hints: ClassVar[dict[str, OptimizerHint]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # TODO(spec-foundation 0.0.4): split this method into a
        # collection-only phase described in ``docs/spec-foundation.md``.
        # Required
        # changes (Phase 4 of the phased implementation order):
        #   - Replace the eager ``"get_queryset" in cls.__dict__`` flip
        #     with ``_detect_custom_get_queryset(cls)`` (MRO-aware) so
        #     abstract bases keep propagating the sentinel. The MRO
        #     walk runs UNCONDITIONALLY before the ``meta is None``
        #     early return.
        #   - After the ``meta is None`` early return, add the
        #     post-finalization registration guard. The guard checks
        #     ``registry.is_finalized()`` and raises ``ConfigurationError``
        #     with the canonical "finalize_django_types() already ran"
        #     message from the spec. This branch must remain reachable
        #     AFTER finalization so abstract bases without ``Meta`` never
        #     trip the guard.
        #   - Snapshot consumer-authored relation fields BEFORE any
        #     synthesis: union of (a) names already in
        #     ``cls.__dict__["__annotations__"]`` and (b) names whose
        #     ``cls.__dict__`` value is consumer-supplied (not a Django
        #     manager/descriptor). Feeds
        #     ``DjangoTypeDefinition.consumer_authored_fields``.
        #   - Replace ``_build_annotations(cls, fields)`` with a
        #     per-field dispatch that:
        #       * routes scalars through ``convert_scalar``
        #       * for relations: skips consumer-authored names entirely
        #         (no synthesis, no pending record); resolves immediately
        #         when ``registry.get(field.related_model)`` returns a
        #         type; otherwise appends a ``PendingRelation`` and
        #         installs a sentinel placeholder annotation that the
        #         finalizer rewrites.
        #   - Build ``DjangoTypeDefinition`` and stash it on the class
        #     as ``cls.__django_strawberry_definition__``. Mirror
        #     ``field_map`` / ``optimizer_hints`` /
        #     ``_is_default_get_queryset`` to the legacy class attrs for
        #     one minor version (compat for the walker).
        #   - Register the model/type pair early via ``registry.register``
        #     and store the definition via
        #     ``registry.register_definition``; record pending relations
        #     via ``registry.add_pending_relation``.
        #   - REMOVE the ``_attach_relation_resolvers(cls, fields)``
        #     call below; resolver attachment moves to
        #     ``finalize_django_types()`` and consumes
        #     ``definition.selected_fields`` with
        #     ``skip_field_names=definition.consumer_authored_fields``.
        #   - REMOVE the trailing ``strawberry.type(cls, ...)`` call;
        #     finalization runs once per class inside
        #     ``finalize_django_types()`` after every pending relation
        #     has been resolved.
        #
        # The docstring below describes the CURRENT 0.0.3 pipeline; it
        # will be rewritten to describe the collection-only phase when
        # this slice ships.
        """Validate ``Meta`` and assemble the Strawberry type.

        Pipeline order:

        1. If the subclass declares its own ``get_queryset``, flip
           ``cls._is_default_get_queryset`` to ``False``. Runs
           **unconditionally** — before the
           ``meta is None`` early return — so an intermediate abstract
           base (no ``Meta``, but its own ``get_queryset``) still flips
           the flag, and any concrete subclass that inherits from such
           a base reports ``has_custom_get_queryset()`` correctly.
        2. Resolve ``cls.Meta``. If absent, skip the rest of the
           pipeline — intermediate abstract subclasses without ``Meta``
           are allowed.
        3. ``_validate_meta(meta)`` — raises ``ConfigurationError`` for
           missing model, ``fields``/``exclude`` collision, or any key
           in ``DEFERRED_META_KEYS``.
        4. ``_select_fields(meta)`` — produce the Meta-filtered Django
           field list once and reuse it for steps 5 and 8 below.
        5. ``_build_annotations(cls, fields)`` — synthesizes the
           ``{name: type}`` mapping by dispatching each field through
           ``converters.convert_scalar`` / ``converters.convert_relation``.
        6. ``cls.__annotations__ = {**synthesized, **existing}`` —
           installs the synthesized annotation map. Consumer-declared
           annotations are merged on top as an implementation detail,
           but ``@strawberry.type`` rewrites ``cls.__annotations__``
           from its own field metadata downstream, so the merge is
           **not** a reliable consumer-override contract in 0.0.3.
        7. ``registry.register(meta.model, cls)`` — claims the model.
        8. ``_attach_relation_resolvers(cls, fields)`` attaches a
           cardinality-aware resolver per relation field (forward FK /
           OneToOne, reverse FK / M2M, reverse OneToOne) so Strawberry's
           default ``getattr`` resolver does not see a Django
           ``RelatedManager``. Lives in ``types.resolvers``; caller passes
           the pre-computed field list to keep the field walk single-pass
           and the dependency direction one-way (``base`` -> ``resolvers``,
           never the reverse).
        9. ``strawberry.type(cls)`` — finalizes the class as a
           Strawberry type with ``Meta.name`` and ``Meta.description``.
           (``Meta.interfaces`` is reserved by ``DEFERRED_META_KEYS``
           pending a future relay spec.)
        """
        super().__init_subclass__(**kwargs)
        # TODO(spec-foundation 0.0.4): replace this single-class
        # ``"get_queryset" in cls.__dict__`` check with a call to a new
        # MRO-walking helper ``_detect_custom_get_queryset(cls)`` and
        # propagate the result through
        # ``DjangoTypeDefinition.has_custom_get_queryset``. The class-attr
        # mirror below stays for one minor version. See ``docs/spec-foundation.md``
        # "Should redo now" for why a class-dict-only check is
        # insufficient (abstract tenant-scoped mixins must propagate).
        # Flip the class-level flag if *this* class declared its own
        # ``get_queryset``. Runs unconditionally — before the
        # ``meta is None`` early return — so an intermediate abstract
        # base (no ``Meta``, but its own ``get_queryset``) still flips
        # the flag for any concrete subclass that inherits from it. The
        # optimizer consumes this for its downgrade-to-Prefetch rule.
        if "get_queryset" in cls.__dict__:
            cls._is_default_get_queryset = False
        meta = cls.__dict__.get("Meta")
        if meta is None:
            # Intermediate abstract subclasses (no ``Meta``) opt out of
            # the rest of the pipeline. Concrete consumer types must
            # declare ``Meta``.
            return
        # TODO(spec-foundation 0.0.4): immediately after the ``meta is
        # None`` early return above, raise ``ConfigurationError`` when
        # ``registry.is_finalized()`` is True so a ``DjangoType`` declared
        # after ``finalize_django_types()`` ran fails loud with the
        # canonical message ("finalize_django_types() already ran; "
        # "cannot register <TypeName> after finalization. Call "
        # "registry.clear() first if this is a test."). Test isolation
        # depends on ``registry.clear()`` resetting the finalized flag.
        _validate_meta(meta)
        # Compute the Meta-selected field list once and reuse it for both
        # annotation synthesis and resolver attachment so the field walk
        # is not duplicated and ``types.resolvers`` does not need to
        # import back into ``types.base``.
        fields = _select_fields(meta)
        _validate_optimizer_hints_against_selected_fields(meta, fields)
        # TODO(spec-foundation 0.0.4): build a ``DjangoTypeDefinition``
        # from the selected fields, optimizer hints,
        # ``has_custom_get_queryset`` flag, and the consumer-authored
        # field set; stash it on ``cls.__django_strawberry_definition__``;
        # call ``registry.register_definition(cls, definition)``. The
        # three ``cls._optimizer_*`` / ``cls._is_default_get_queryset``
        # writes below stay for one minor version as a compat mirror so
        # the walker's ``getattr`` reads keep working without a same-slice
        # rewrite. See ``docs/spec-foundation.md`` step 13 of the
        # collection pseudocode.
        # B7: precompute optimizer field metadata so the walker can
        # skip _meta.get_fields() on every walk.
        cls._optimizer_field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}
        # B4: stash optimizer_hints for the walker to consult.
        cls._optimizer_hints = _meta_optimizer_hints(meta)
        # TODO(spec-foundation 0.0.4): before calling _build_annotations,
        # snapshot consumer-authored relation fields (annotation OR
        # class-dict assignment that is not a Django manager/descriptor)
        # and pass that frozenset into the per-field dispatch so neither
        # placeholder synthesis nor pending-relation recording happens
        # for those names. The set also feeds
        # ``DjangoTypeDefinition.consumer_authored_fields`` so the
        # finalizer's resolver-attachment phase can skip them. See
        # ``docs/spec-foundation.md`` "Manual annotation contract for
        # relation fields (0.0.4)".
        synthesized = _build_annotations(cls, fields)
        # Implementation detail (NOT a stable consumer-override contract
        # in 0.0.3): consumer-declared annotations are merged on top of
        # the synthesized ones in the dict literal below, but
        # ``@strawberry.type`` rewrites ``cls.__annotations__`` from
        # its own field metadata downstream, so the merge does not
        # reliably preserve the override. The skipped
        # ``test_consumer_annotation_overrides_synthesized`` pins the
        # current limitation until a future consumer-overrides design
        # defines the stable mechanism.
        existing = dict(cls.__dict__.get("__annotations__", {}))
        cls.__annotations__ = {**synthesized, **existing}
        registry.register(meta.model, cls)
        # TODO(spec-foundation 0.0.4): REMOVE the
        # ``_attach_relation_resolvers(cls, fields)`` call below.
        # Resolver attachment moves to ``finalize_django_types()`` and
        # consumes ``definition.selected_fields`` with
        # ``skip_field_names=definition.consumer_authored_fields`` so
        # consumer-supplied ``strawberry.field(resolver=...)`` /
        # ``@strawberry.field`` shapes are never clobbered. See
        # ``docs/spec-foundation.md`` "Finalization phase" Phase 2.
        # Attach cardinality-aware resolvers per relation field. Without
        # this, Strawberry's default ``getattr`` resolver returns a
        # Django ``RelatedManager`` for reverse rels / M2M and Strawberry
        # rejects with "Expected Iterable". Must run before
        # ``strawberry.type(cls)`` so the field metadata is in place when
        # Strawberry processes the class.
        _attach_relation_resolvers(cls, fields)
        # TODO(future relay spec): when relay support lands, the
        # implementation will inject ``Meta.interfaces`` (e.g.,
        # ``relay.Node``) into ``cls.__bases__`` before strawberry.type
        # processes the class, and ``"interfaces"`` will move from
        # ``DEFERRED_META_KEYS`` back into ``ALLOWED_META_KEYS``.
        # Until then the key is rejected by ``_validate_meta`` so it
        # cannot be set silently. Consumers wanting a Strawberry
        # interface today should subclass it directly:
        # ``class CategoryType(DjangoType, relay.Node): ...``.
        name = getattr(meta, "name", None)
        description = getattr(meta, "description", None)
        # TODO(spec-foundation 0.0.4): REMOVE this
        # ``strawberry.type(cls, ...)`` call. Strawberry finalization
        # moves into ``finalize_django_types()`` (new module
        # ``types/finalizer.py``) per ``docs/spec-foundation.md``
        # "Strawberry finalization strategy". Pinned by Spike A's
        # five pass criteria — production code in this slice cannot
        # land until the spike confirms deferred ``strawberry.type(cls)``
        # is safe.
        strawberry.type(cls, name=name, description=description)

    @classmethod
    def get_queryset(
        cls,
        queryset: models.QuerySet,
        info: Any,
        **kwargs: Any,
    ) -> models.QuerySet:
        """Default identity hook.

        Subclasses override this to scope visibility (permissions,
        multi-tenancy, soft-delete). The optimizer detects overrides via
        ``has_custom_get_queryset`` and downgrades ``select_related`` to
        ``Prefetch`` so visibility filters apply across joins.
        """
        return queryset

    @classmethod
    def has_custom_get_queryset(cls) -> bool:
        """Return ``True`` if this subclass (or any intermediate base) overrides ``get_queryset``.

        Used by ``DjangoOptimizerExtension`` to decide whether a related-
        field traversal should be downgraded to a ``Prefetch``.

        Implementation: ``__init_subclass__`` flips
        ``_is_default_get_queryset`` to ``False`` at class-creation time
        when the subclass declares its own ``get_queryset``; this method
        returns the negated flag for a constant-time attribute read.
        Inheritance walks naturally — a subclass without its own
        ``get_queryset`` whose parent declared one inherits the parent's
        ``False`` sentinel through the class hierarchy.
        """
        # TODO(spec-foundation 0.0.4): rewrite as a thin lookup against
        # the new definition object:
        #   ``return cls.__django_strawberry_definition__.has_custom_get_queryset``
        # ``walker.py:42`` keeps reading the same shape so no walker
        # change is required in this slice. See ``docs/spec-foundation.md``
        # "Should redo now".
        return not cls._is_default_get_queryset


def _meta_optimizer_hints(meta: type) -> dict[str, Any]:
    """Return ``meta.optimizer_hints`` as a dict, or ``{}`` when unset/empty.

    Centralizes the ``getattr(meta, "optimizer_hints", None) or {}`` pattern
    used across ``__init_subclass__`` and the validators so the Meta key
    name only appears once at the read site.
    """
    return getattr(meta, "optimizer_hints", None) or {}


def _format_unknown_fields_error(*, model: type, attr: str, unknown: list[str], available: set[str]) -> str:
    """Return the standard "unknown fields … Available: …" error message.

    Used by every validator that points at a typo in ``Meta.fields``,
    ``Meta.exclude``, or ``Meta.optimizer_hints``.  Centralizing the
    format keeps the consumer-visible error shape consistent across
    typo-guard sites.
    """
    return f"{model.__name__}.Meta.{attr} names unknown fields: {unknown}. Available: {sorted(available)}."


def _validate_meta(meta: type) -> None:
    """Validate a ``DjangoType`` subclass's nested ``Meta`` class.

    Validation order:

    1. ``Meta.model`` is required.
    2. ``fields`` and ``exclude`` are mutually exclusive.
    3. Any key in ``DEFERRED_META_KEYS`` raises with a clear message.
    4. Any non-dunder key on ``meta`` not in ``ALLOWED_META_KEYS |
       DEFERRED_META_KEYS`` raises (typo guard).

    Raises:
        ConfigurationError: any of the above violations.
    """
    if getattr(meta, "model", None) is None:
        raise ConfigurationError("Meta.model is required")

    declared = {k for k in meta.__dict__ if not k.startswith("_")}

    if "fields" in declared and "exclude" in declared:
        raise ConfigurationError("Meta.fields and Meta.exclude are mutually exclusive")

    deferred = sorted(declared & DEFERRED_META_KEYS)
    if deferred:
        raise ConfigurationError(
            f"Meta keys not supported yet: {deferred}. The feature that owns them has not shipped.",
        )

    unknown = sorted(declared - ALLOWED_META_KEYS - DEFERRED_META_KEYS)
    if unknown:
        raise ConfigurationError(f"Unknown Meta keys: {unknown}")

    # B4: validate optimizer_hints field names and value types.
    hints = _meta_optimizer_hints(meta)
    if hints:
        model = meta.model
        valid_field_names = {f.name for f in model._meta.get_fields()}
        unknown_hint_fields = sorted(set(hints) - valid_field_names)
        if unknown_hint_fields:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="optimizer_hints",
                    unknown=unknown_hint_fields,
                    available=valid_field_names,
                ),
            )
        bad_values = sorted(k for k, v in hints.items() if not isinstance(v, OptimizerHint))
        if bad_values:
            raise ConfigurationError(
                f"optimizer_hints values must be OptimizerHint instances, "
                f"got non-OptimizerHint for: {bad_values}",
            )


def _validate_optimizer_hints_against_selected_fields(meta: type, fields: list[Any]) -> None:
    """Reject ``optimizer_hints`` keys that are not in the type's selected fields.

    ``_validate_meta`` already checks that hint keys name real Django fields
    on ``meta.model``.  This second check catches the silent-dead-code
    case where the field is real but excluded from the GraphQL type via
    ``Meta.fields`` / ``Meta.exclude`` — the walker never visits it, so
    the consumer's optimization intent is lost.
    """
    hints = _meta_optimizer_hints(meta)
    if not hints:
        return
    selected_names = {f.name for f in fields}
    excluded_hint_fields = sorted(set(hints) - selected_names)
    if excluded_hint_fields:
        raise ConfigurationError(
            f"{meta.model.__name__}.Meta.optimizer_hints names fields not in the type's "
            f"selected fields: {excluded_hint_fields}.  Selected: {sorted(selected_names)}.",
        )


def _select_fields(meta: type) -> list[Any]:
    """Filter ``meta.model._meta.get_fields()`` per ``Meta.fields`` / ``Meta.exclude``.

    Called once from ``DjangoType.__init_subclass__`` and the resulting
    list is reused by ``_build_annotations`` (in this module) and
    ``_attach_relation_resolvers`` (in ``types.resolvers``) so the field
    walk does not happen twice. Iteration order follows
    Django's ``_meta.get_fields()`` so the generated GraphQL type's field
    order matches Django's declared order, with reverse-side relations
    appended at the end.

    Selection rules:

    - ``fields == "__all__"`` (or both ``fields``/``exclude`` unset) ->
      every concrete + relation field.
    - ``fields`` as a sequence -> only those names; unknown names raise.
    - ``exclude`` as a sequence -> every field except those names;
      unknown names raise.

    Raises:
        ConfigurationError: ``Meta.fields`` or ``Meta.exclude`` names a
            field that does not exist on ``Meta.model``. The error names
            the model, the unknown values, and the available field set
            so typos surface loudly instead of silently dropping.
    """
    model = meta.model
    fields_spec = getattr(meta, "fields", None)
    exclude_spec = getattr(meta, "exclude", None)

    all_fields = list(model._meta.get_fields())
    all_names = [f.name for f in all_fields]
    valid_names = set(all_names)

    if fields_spec == "__all__" or (fields_spec is None and exclude_spec is None):
        selected_names = valid_names
    elif fields_spec is not None:
        unknown = sorted(set(fields_spec) - valid_names)
        if unknown:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="fields",
                    unknown=unknown,
                    available=valid_names,
                ),
            )
        selected_names = set(fields_spec)
    else:
        unknown = sorted(set(exclude_spec) - valid_names)
        if unknown:
            raise ConfigurationError(
                _format_unknown_fields_error(
                    model=model,
                    attr="exclude",
                    unknown=unknown,
                    available=valid_names,
                ),
            )
        selected_names = valid_names - set(exclude_spec)

    return [f for f in all_fields if f.name in selected_names]


# TODO(spec-foundation 0.0.4): rewrite this function as a per-field
# dispatch that returns ``(annotations, pending)`` per
# ``docs/spec-foundation.md`` "Collection phase" step 8. The relation
# branch must:
#   - skip names in the caller-provided ``consumer_authored_fields``
#     frozenset (no synthesis, no pending record)
#   - if ``registry.get(field.related_model)`` returns a type, install
#     the concrete annotation immediately
#   - otherwise append a ``PendingRelation`` to the pending list and
#     install a sentinel placeholder annotation that the finalizer
#     rewrites in phase 1
# The eager ``ConfigurationError`` from ``convert_relation`` goes away;
# the same error format moves into
# ``finalizer._format_unresolved_targets_error`` and only fires after
# every ``DjangoType`` has had a chance to register.
def _build_annotations(cls: type, fields: list[Any]) -> dict[str, Any]:
    """Build the annotation dict the Strawberry type decorator consumes.

    Field-by-field dispatch: every entry in ``fields`` is routed through
    ``convert_relation`` if ``field.is_relation`` is true, or
    ``convert_scalar`` otherwise. The caller pre-computes the list with
    ``_select_fields(meta)`` so this function does not need ``meta``.

    Args:
        cls: The consumer-facing ``DjangoType`` subclass (its ``__name__``
            threads into ``convert_scalar`` so generated choice enums
            carry a stable name).
        fields: The Meta-filtered list of Django field objects.

    Returns:
        A dict suitable for ``cls.__annotations__.update(...)``.

    Raises:
        ConfigurationError: a relation field's target ``DjangoType`` is not
            yet registered (raised by ``convert_relation``); or an
            unsupported scalar field type is encountered (raised by
            ``convert_scalar``).
    """
    annotations: dict[str, Any] = {}
    for field in fields:
        if field.is_relation:
            annotations[field.name] = convert_relation(field)
        else:
            annotations[field.name] = convert_scalar(field, cls.__name__)
    return annotations
