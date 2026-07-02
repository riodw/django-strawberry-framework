"""The ``SerializerMutation`` base + ``Meta`` validation + the phase-2.5 bind (spec-039 Slice 2).

The DRF-serializer write surface, riding the ``036`` mutation seams
(``mutations/sets.py``) exactly as ``038``'s ``DjangoModelFormMutation`` does
(spec-039 Decision 6 - the ``ModelSerializer``-rides-``DjangoMutation`` choice):

- ``SerializerMutation`` subclasses ``DjangoMutation`` and overrides the SAME seam
  set ``DjangoModelFormMutation`` overrides (``_resolve_model`` ->
  ``Meta.serializer_class.Meta.model``, ``_validate_meta`` -> the serializer
  matrix, ``build_input`` -> the ``rest_framework/inputs.py`` generator,
  ``input_type_name`` / ``input_module_path`` -> the serializer-input namespace).
  It rides the ``DjangoMutation`` metaclass + declaration registry +
  ``bind_mutations()`` UNCHANGED - no new metaclass, no new declaration registry,
  no ``bind_serializer_mutations()`` (the dividend of Decision 6) - so a
  serializer mutation binds its model-backed ``<Name>Payload`` (``node`` /
  ``result`` slot) through the same phase-2.5 path as the ``036`` model mutation
  and the ``038`` ``ModelForm`` mutation.

The serializer ``_validate_meta`` (Decision 6 / Decision 10 / Decision 11):
``Meta.serializer_class`` is required and must be a DRF ``serializers.Serializer``
subclass; for the ``ModelSerializer``-driven contract it must be a
``serializers.ModelSerializer`` with a resolvable ``Meta.model`` (a
non-``ModelSerializer`` or a ``ModelSerializer`` with no ``Meta.model`` raises a
targeted ``ConfigurationError``); the check runs BEFORE ``_resolve_model`` so a
missing / wrong-type ``serializer_class`` is a clean error, never a raw
``AttributeError``. ``operation`` is ``create`` / ``update`` only (``"delete"``
rejected - DRF serializers do not delete, Decision 10). The allowed-key set ADDS
``serializer_class`` / ``optional_fields``, KEEPS ``operation`` / ``fields`` /
``exclude`` / ``permission_classes`` (the ``036`` write-auth seam inherited
unchanged, Decision 11), and DROPS ``model`` / ``input_class`` /
``partial_input_class``; ``Meta.fields`` / ``Meta.exclude`` are mutually
exclusive. Field narrowing + ``optional_fields`` reuse the Slice-1
``rest_framework/inputs.py`` machinery, never a re-spelled copy.

**The whole module is behind the DRF soft-import guard (Decision 12).** It
``import``s ``rest_framework.serializers`` at module top, so importing this module
requires DRF; the root ``__getattr__`` (and ``rest_framework/__init__.py``'s
``require_drf()``) gate that import for a DRF-absent consumer.

**Slice 3 landed the resolver seams + the serializer-construction hook bodies.** The
``resolve_sync`` / ``resolve_async`` serializer-pipeline overrides (below) delegate
to ``rest_framework/resolvers.py::resolve_serializer_sync`` /
``resolve_serializer_async`` - the D8 carry-forward Slice 2 deferred because the
resolver module did not exist yet (an inert Slice-2 declaration inherited
``DjangoMutation``'s callable pair; Slice 3 lands BOTH the overrides here AND the
resolver bodies, the same slice/resolver-existence pairing the form flavor used in
``forms/sets.py``). The default ``get_serializer_kwargs`` construction hook ships
here so ``build_input``'s ``_hook_overridden`` waiver has a base to compare against
(the ``forms/sets.py`` ``get_form_kwargs`` precedent); the Slice-3 resolver consumes
``get_serializer_kwargs`` (the hook the spec D8 step 4 names) and OWNS the framework
merge / ``partial`` injection / ``context["request"]`` / H3 ``ConfigurationError``
rules on top of its return, so those framework-owned invariants never live in the
consumer-overridable hook. The serializer flavor deliberately has **no** coarse
``get_serializer`` constructor hook (unlike the form flavor's ``get_form``): its H3
invariants - ``partial`` and the authorized-actor ``context["request"]`` - cannot be
entrusted to a consumer-overridable constructor, so construction is framework-owned
through ``_merged_serializer_kwargs`` (spec-039 Medium-7).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rest_framework import serializers

from ..exceptions import ConfigurationError
from ..mutations.inputs import CREATE
from ..mutations.sets import (
    NON_DELETE_OPERATION_INPUT_KIND,
    NON_DELETE_WRITE_OPERATIONS,
    DjangoMutation,
    _hook_overridden,
    _ValidatedMutationMeta,
    build_and_stash_input,
    construction_kwargs,
    non_delete_operation_error,
    reject_unknown_meta_keys,
    require_backing_class,
    resolve_backed_model_or_raise,
    resolve_meta_model,
    resolver_seams,
)
from ..mutations.sets import (
    _validate_permission_classes as _validate_mutation_permission_classes,
)
from ..utils.inputs import normalize_field_name_sequence
from .inputs import (
    SERIALIZER_INPUTS_MODULE_PATH,
    NestedSerializerConfig,
    _serializer_shape_build_cache,
    build_serializer_input_class,
    guard_create_required_serializer_fields,
    materialize_serializer_input_class,
    resolve_effective_serializer_fields,
    resolve_injected_field_specs,
    resolve_optional_fields,
    serializer_schema_fingerprint,
)
from .inputs import (
    get_serializer_for_schema as _default_serializer_schema_fields,
)
from .serializer_converter import is_nested_serializer_field

# The serializer ``Meta``'s allowed-key set (spec-039 Decision 6). Disjoint from
# ``036``'s ``_ALLOWED_MUTATION_META_KEYS`` and ``038``'s form sets: a serializer
# ``Meta`` ADDS ``serializer_class`` / ``optional_fields``, KEEPS ``operation`` /
# ``fields`` / ``exclude`` / ``permission_classes`` (the ``036`` write-auth seam
# inherited unchanged - Decision 11), and DROPS ``model`` / ``input_class`` /
# ``partial_input_class``.
_ALLOWED_SERIALIZER_META_KEYS: frozenset[str] = frozenset(
    {
        "serializer_class",
        "optional_fields",
        "injected_fields",
        "select_for_update",
        "nested_fields",
        "operation",
        "fields",
        "exclude",
        "permission_classes",
    },
)

# ``operation`` -> input-generator kind: the shared
# ``mutations/sets.py::NON_DELETE_OPERATION_INPUT_KIND`` map (spec-039 Mn2), which
# replaced the byte-identical ``_SERIALIZER_OPERATION_INPUT_KIND`` /
# ``_modelform_operation_kind`` copies. ``create`` -> the required-aware
# ``<Serializer>Input`` (``CREATE``); ``update`` -> the all-optional
# ``<Serializer>PartialInput`` (``PARTIAL``).


def _checked_schema_field_map(
    cls: type,
    meta: _ValidatedMutationMeta,
) -> dict[str, serializers.Field]:
    """Read ``get_serializer_for_schema()`` through the ONE guarded path (spec-039 #10 / rev2 P2).

    The single authoritative read of the schema hook for the bind window: calls the overridable
    ``get_serializer_for_schema()`` and, when the class-validation fingerprint is present on the
    snapshot, verifies the returned shape has NOT DRIFTED (a nondeterministic hook that validates
    one shape and binds / names another is a clear ``ConfigurationError``). Both ``build_input``
    and ``input_type_name`` route through here, so the type-name derivation cannot read an
    unguarded field map behind the fingerprint's back.

    The fingerprint is over the EFFECTIVE (writable + narrowed) field set - the SAME set the
    input build uses (rev6 #17 review P1) - so a read-only / narrowed-away nested serializer is
    never descended into; the RAW ``field_map`` is still returned for the build to re-narrow. The
    recursion is gated on ``meta.nested_fields`` (the opt-in tree, rev6 #17 review P2), the SAME map
    passed at class validation, so both windows fingerprint the identical opt-in structure and an
    unopted nested field is never descended into.
    """
    field_map = cls.get_serializer_for_schema()
    if meta.schema_fingerprint is not None:
        effective = resolve_effective_serializer_fields(
            meta.serializer_class,
            fields=meta.fields,
            exclude=meta.exclude,
            field_map=field_map,
        )
        if (
            serializer_schema_fingerprint(effective, nested_configs=meta.nested_fields)
            != meta.schema_fingerprint
        ):
            raise ConfigurationError(
                f"SerializerMutation {cls.__name__}.get_serializer_for_schema() returned a "
                "DIFFERENT field shape at bind than at class validation; the hook must be "
                "deterministic and request-independent (the input is generated once at "
                "finalization). Return a stable field map (do not read request state or "
                "mutate per call).",
            )
    return field_map


def _serializer_input_shape_for(
    meta: _ValidatedMutationMeta,
    *,
    operation_kind: str,
    field_map: dict[str, serializers.Field],
) -> tuple[type, Any]:
    """Return the serializer input class + descriptor through the shared shape cache (Mn5)."""
    input_cls, shape = build_serializer_input_class(
        meta.serializer_class,
        operation_kind=operation_kind,
        fields=meta.fields,
        exclude=meta.exclude,
        optional_fields=meta.optional_fields,
        field_map=field_map,
        # rev6 #17: opt-in nested serializer inputs, built recursively during the walk.
        nested_configs=meta.nested_fields,
    )
    cached = _serializer_shape_build_cache.get(shape.cache_key)
    if cached is not None:
        return cached
    _serializer_shape_build_cache[shape.cache_key] = (input_cls, shape)
    return input_cls, shape


# ``operation`` -> the DRF serializer write method whose OVERRIDE ``Meta.nested_fields`` requires
# (spec-039 rev6 #17): a create routes nested data through ``create()``, an update through
# ``update()``. DRF's ``ModelSerializer.create`` / ``.update`` ``assert`` (via
# ``raise_errors_on_nested_writes``) that no nested writable data is present unless the method is
# overridden - a raw ``AssertionError`` that would escape the error envelope - so the framework
# requires the override at class creation instead (the "only pass nested data to serializers that
# implement create()/update()" contract).
_SERIALIZER_OPERATION_NESTED_WRITE_METHOD: dict[str, str] = {
    "create": "create",
    "update": "update",
}


def _validate_serializer_nested_fields(
    name: str,
    serializer_class: type[serializers.Serializer],
    operation: str,
    field_map: dict[str, serializers.Field],
    nested_fields: Any,
) -> dict[str, NestedSerializerConfig] | None:
    """Validate + normalize ``Meta.nested_fields`` at class creation (spec-039 rev6 #17).

    ``Meta.nested_fields`` is the explicit opt-in for nested serializer writes: a
    ``{field_name: NestedSerializerConfig}`` map. Validated all at class creation:

    - it must be a mapping of ``str -> NestedSerializerConfig`` (a wrong container / wrong value
      type fails loud);
    - each key must name a field in the schema-time ``field_map`` that IS a nested
      ``Serializer`` / ``ListSerializer`` (a typo / non-nested field fails loud - the deeper
      per-level key validation runs in the recursive build);
    - the serializer MUST override the write method the ``operation`` uses (``create()`` for
      create, ``update()`` for update): DRF's default ``ModelSerializer`` method ``assert``s
      against nested writable data (a raw ``AssertionError`` that would escape the envelope), so
      the framework requires the override up front - the "only pass nested data to a serializer
      that implements the nested write correctly" contract. The framework NEVER auto-saves the
      nested relation; the serializer author's overridden method owns the write.

    Returns the normalized ``dict`` (``None`` when unset).
    """
    if nested_fields is None:
        return None
    if not isinstance(nested_fields, Mapping):
        raise ConfigurationError(
            f"SerializerMutation {name}.Meta.nested_fields must be a mapping of "
            f"{{field_name: NestedSerializerConfig}}; got {nested_fields!r}.",
        )
    normalized: dict[str, NestedSerializerConfig] = {}
    for field_name, config in nested_fields.items():
        if not isinstance(config, NestedSerializerConfig):
            raise ConfigurationError(
                f"SerializerMutation {name}.Meta.nested_fields[{field_name!r}] must be a "
                f"NestedSerializerConfig; got {config!r}.",
            )
        field = field_map.get(field_name)
        if field is None:
            raise ConfigurationError(
                f"SerializerMutation {name}.Meta.nested_fields names {field_name!r}, which is not "
                "in the serializer's schema-time field map. Nest only fields the serializer "
                "declares.",
            )
        if not is_nested_serializer_field(field):
            raise ConfigurationError(
                f"SerializerMutation {name}.Meta.nested_fields names {field_name!r}, but it is a "
                f"{type(field).__name__}, not a nested serializer. nested_fields is only for "
                "nested Serializer / ListSerializer fields (a relation is a "
                "PrimaryKeyRelatedField).",
            )
        normalized[field_name] = config
    write_method = _SERIALIZER_OPERATION_NESTED_WRITE_METHOD[operation]
    if getattr(serializer_class, write_method) is getattr(
        serializers.ModelSerializer,
        write_method,
    ):
        raise ConfigurationError(
            f"SerializerMutation {name}.Meta.nested_fields is declared, but {serializer_class.__name__} "
            f"does not override {write_method}(); DRF's default ModelSerializer.{write_method}() "
            "raises on writable nested data (an AssertionError that would escape the error "
            f"envelope). Implement {write_method}() to perform the nested write yourself (the "
            "framework decodes + validates the nested data but never auto-saves the relation), or "
            "remove Meta.nested_fields.",
        )
    return normalized


class SerializerMutation(DjangoMutation):
    """A DRF-``ModelSerializer``-backed write mutation (spec-039 Decision 6).

    Rides the ``DjangoMutation`` base: the SAME metaclass validates its ``Meta``
    (through the ``_validate_meta`` override below), the SAME declaration registry
    records it, and the SAME ``bind_mutations()`` phase-2.5 bind resolves its
    model's primary ``DjangoType`` + materializes its model-backed ``<Name>Payload``
    (``node`` / ``result`` slot). The serializer-specific behavior is the seam
    overrides: the model comes from ``Meta.serializer_class.Meta.model``, the input
    is serializer-derived (``rest_framework/inputs.py``), and the input namespace is
    ``rest_framework.inputs``.

    A concrete subclass declares ``Meta.serializer_class`` (a
    ``serializers.ModelSerializer`` subclass with a concrete ``Meta.model``) +
    ``Meta.operation in {"create", "update"}`` (plus optional ``Meta.fields`` /
    ``Meta.exclude`` / ``Meta.optional_fields`` / ``Meta.permission_classes``).
    """

    # The serializer-input namespace (``rest_framework.inputs``), overriding the
    # ``036`` model default (``mutations.inputs``) so a serializer mutation's lazy
    # ``data:`` ref resolves the serializer-derived input, not a model-column input.
    input_module_path: str = SERIALIZER_INPUTS_MODULE_PATH

    # The Slice-1 reverse-map records (``InputFieldSpec`` per input field), stashed
    # at bind so the Slice-3 decode reaches the serializer-field-keyed reverse map.
    # ``None`` until bind (mirrors ``_input_class`` + the form flavor's slot).
    _input_field_specs: list | None = None

    # The schema-time specs for ``Meta.injected_fields`` (spec-039 rev6 rev2 P1), stashed at
    # bind so the Slice-3 resolver holds each injected field to the SAME runtime-agreement
    # contract (present / writable / source / kind / relation-model) an input field gets - not
    # merely that its key is present in ``data``. ``[]`` when no fields are injected.
    _injected_field_specs: list | None = None

    # The bound serializer-input type name, stashed after successful materialization.
    # Before bind, ``input_type_name`` derives the descriptor through the shared
    # cache helper; after bind, it can read this once the determinism guard passes.
    _input_type_name: str | None = None

    @classmethod
    def _resolve_model(cls, meta: type) -> Any:
        """Resolve the model from ``Meta.serializer_class.Meta.model`` (the ``036`` seam override).

        Returns ``None`` for a missing ``serializer_class`` / a serializer with no
        ``Meta`` / a ``ModelSerializer`` whose ``Meta.model`` is unset.
        ``_validate_meta`` has already validated ``serializer_class`` presence +
        ``ModelSerializer``-subclass-hood BEFORE calling this (mirroring the form
        flavor's ``_resolve_model`` ordering), so a ``None`` return here means "a
        ``ModelSerializer`` with no resolvable model" - the base validation raises a
        clean ``ConfigurationError`` (never a raw ``AttributeError`` from
        ``serializer_class.Meta.model``).
        """
        return resolve_meta_model(meta, key="serializer_class", meta_attr="Meta")

    @classmethod
    def _validate_meta(cls, meta: type) -> _ValidatedMutationMeta:
        """Validate a serializer-mutation ``Meta`` at class creation (spec-039 Decision 6).

        The serializer matrix (raising ``ConfigurationError`` naming the offending
        key), all at class creation:

        - **unknown ``Meta`` key** - the promoted ``reject_unknown_meta_keys`` typo
          guard over ``_ALLOWED_SERIALIZER_META_KEYS``.
        - **missing ``serializer_class``** - a clean error naming the key.
        - **``serializer_class`` not a DRF ``serializers.Serializer``** - the broad
          type gate.
        - **``serializer_class`` not a ``serializers.ModelSerializer``** - the
          ``ModelSerializer``-driven contract (Decision 6); a plain ``Serializer``
          (incl. model-less) is rejected naming the requirement.
        - **no resolvable ``Meta.model``** - a ``ModelSerializer`` with no model
          raises (``_resolve_model`` returns ``None``). All serializer-type checks
          run BEFORE ``_resolve_model`` so a wrong-type / model-less serializer is a
          clean error, never a raw ``AttributeError``.
        - **bad ``operation``** - missing or not in ``NON_DELETE_WRITE_OPERATIONS``
          (``"delete"`` rejected - DRF serializers do not delete, Decision 10) via
          the shared ``non_delete_operation_error``.
        - **``fields`` + ``exclude`` both supplied / bare-string (incl.
          ``"__all__"``) / duplicate / unknown-name / empty-set** - via the Slice-1
          ``resolve_effective_serializer_fields``, which calls the shared
          ``utils/inputs.py::normalize_field_name_sequence(flavor="SerializerMutation")``
          DIRECTLY - the required keyword-only ``flavor`` arg exists for exactly this
          (P2.7). All three flavors now call that shared helper directly (spec-039 Mn3
          inlined the former model / form re-binding wrappers), so there is no
          per-flavor wrapper on any side.

        ``permission_classes`` is validated + normalized by the shared
        ``_validate_permission_classes`` (the ``DjangoModelPermission`` default when
        unset - the ``036`` write-auth seam, Decision 11). The snapshot carries
        ``serializer_class`` + the resolved ``model``; ``Meta.fields`` /
        ``Meta.exclude`` are stored RAW (``build_input`` re-resolves them - the form
        flavor's validate-then-store-raw precedent, D1). ``Meta.optional_fields`` is
        the MUTATION's own key (spec-039 Critical-1 - NOT the serializer's ``Meta``):
        normalized here (bare-string incl. ``"__all__"`` / duplicate rejected) and
        name-validated against the effective input set, then carried on the snapshot
        (``optional_fields``) so ``build_input`` threads it into the create input
        requiredness + the descriptor identity (re-validated at bind via
        ``resolve_optional_fields``).
        """
        name = cls.__name__
        reject_unknown_meta_keys(
            f"SerializerMutation {name}",
            meta,
            _ALLOWED_SERIALIZER_META_KEYS,
        )

        # The presence clause is the shared ``require_backing_class`` (spec-039 M5);
        # the two serializer-specific type-gates (Serializer, then ModelSerializer)
        # stay here - their messages genuinely diverge from the form flavor's.
        serializer_class = require_backing_class(
            name,
            meta,
            key="serializer_class",
            base_label="SerializerMutation",
            expected_label="serializers.ModelSerializer",
        )
        if not (
            isinstance(serializer_class, type)
            and issubclass(serializer_class, serializers.Serializer)
        ):
            raise ConfigurationError(
                f"SerializerMutation {name}.Meta.serializer_class must be a DRF "
                f"serializers.Serializer subclass; got {serializer_class!r}.",
            )
        if not issubclass(serializer_class, serializers.ModelSerializer):
            raise ConfigurationError(
                f"SerializerMutation {name}.Meta.serializer_class {serializer_class.__name__} "
                "must be a serializers.ModelSerializer with a concrete Meta.model; a plain "
                "serializers.Serializer has no backing model + no DjangoType to return.",
            )

        # The "resolves no model" raise is the shared ``resolve_backed_model_or_raise``
        # (spec-039 M5), run after the type-gates so ``Meta.serializer_class`` is a
        # real class with a ``.__name__``.
        model = resolve_backed_model_or_raise(
            cls,
            meta,
            base_label="SerializerMutation",
            key="serializer_class",
            noun="ModelSerializer",
        )

        operation = getattr(meta, "operation", None)
        if operation not in NON_DELETE_WRITE_OPERATIONS:
            raise non_delete_operation_error("SerializerMutation", name, operation)

        fields = getattr(meta, "fields", None)
        exclude = getattr(meta, "exclude", None)
        # Discover the schema-time field set ONCE through the OVERRIDABLE
        # ``get_serializer_for_schema()`` classmethod hook (spec-039 Critical-2 /
        # Decision 7), so a serializer whose ``.fields`` cannot be materialized no-arg
        # is validated through the consumer's override - not the default discovery.
        # ``cls._mutation_meta`` is not yet assigned at class creation, so the default
        # hook reads ``cls.Meta.serializer_class`` (the same serializer just validated).
        field_map = cls.get_serializer_for_schema()
        # Validate the narrowing fail-loud via the Slice-1 machinery (mutual
        # exclusion, bare-string incl. ``"__all__"`` / duplicate / unknown-name /
        # empty-set guard), which calls the shared
        # ``normalize_field_name_sequence(flavor="SerializerMutation")`` DIRECTLY
        # (P2.7 promotes the typo-guard / field-sequence MECHANICS). All three flavors
        # call that shared helper directly (spec-039 Mn3 inlined the former model /
        # form re-binding wrappers), so there is no per-flavor wrapper on any side. The
        # snapshot stores the RAW declarations; ``build_input`` re-resolves them (D1 -
        # the form flavor's validate-then-store-raw precedent).
        effective = resolve_effective_serializer_fields(
            serializer_class,
            fields=fields,
            exclude=exclude,
            field_map=field_map,
        )
        # ``Meta.optional_fields`` is the MUTATION's key (spec-039 Critical-1 - the
        # documented public surface, NOT the serializer's own ``Meta``): normalize its
        # SHAPE here (a bare string incl. ``"__all__"`` / a duplicate fail loud at
        # class creation) and validate its NAMES against the effective input set, then
        # carry the normalized tuple on the snapshot so ``build_input`` threads it into
        # the create input requiredness + the ``SerializerInputShape`` descriptor
        # identity. (The bind re-validates names via ``resolve_optional_fields``; this
        # is the earliest-feedback class-creation check.)
        optional_fields = normalize_field_name_sequence(
            getattr(meta, "optional_fields", None),
            label="optional_fields",
            flavor="SerializerMutation",
        )
        resolve_optional_fields(serializer_class, optional_fields, tuple(effective))
        # ``Meta.injected_fields`` (rev6 #2): the auditable, per-field replacement for the
        # blanket get_serializer_kwargs waiver. Normalized here (bare-string / duplicate
        # rejected via the shared helper); ``build_input`` subtracts these from the
        # create-required guard and the resolver verifies they reach the serializer's data.
        injected_fields = normalize_field_name_sequence(
            getattr(meta, "injected_fields", None),
            label="injected_fields",
            flavor="SerializerMutation",
        )
        # rev6 rev2 P1: an injected field must be a real SCHEMA-TIME field (a required field the
        # input narrowed away), validated at class creation so a typo fails loud here rather than
        # silently waiving nothing. The runtime resolver then re-checks it against serializer.fields.
        if injected_fields:
            unknown_injected = [name for name in injected_fields if name not in field_map]
            if unknown_injected:
                raise ConfigurationError(
                    f"SerializerMutation {name}.Meta.injected_fields names field(s) not in the "
                    f"schema-time field map: {sorted(unknown_injected)!r}. Inject only fields the "
                    "serializer's get_serializer_for_schema() exposes.",
                )
        # ``Meta.select_for_update`` (rev6 #14): opt-in row lock on the UPDATE locate. A bool
        # only (the shared locate applies ``.select_for_update()`` when True); a non-bool is a
        # clear class-creation error. On a backend without ``FOR UPDATE`` (e.g. sqlite) Django
        # silently skips the clause, so it is safe to declare regardless of backend.
        select_for_update = getattr(meta, "select_for_update", False)
        if not isinstance(select_for_update, bool):
            raise ConfigurationError(
                f"SerializerMutation {name}.Meta.select_for_update must be a bool; got "
                f"{select_for_update!r}.",
            )
        # ``Meta.nested_fields`` (rev6 #17): the explicit opt-in for nested serializer writes.
        # Validated at class creation - each key must name a nested serializer field the schema
        # map exposes, and the serializer MUST override the operation's write method (create /
        # update), because the framework never auto-saves the nested relation.
        nested_fields = _validate_serializer_nested_fields(
            name,
            serializer_class,
            operation,
            field_map,
            getattr(meta, "nested_fields", None),
        )

        permission_classes = _validate_mutation_permission_classes(
            name,
            getattr(meta, "permission_classes", None),
        )

        return _ValidatedMutationMeta(
            model=model,
            operation=operation,
            input_class=None,
            partial_input_class=None,
            fields=fields,
            exclude=exclude,
            permission_classes=permission_classes,
            serializer_class=serializer_class,
            optional_fields=optional_fields,
            injected_fields=injected_fields,
            select_for_update=select_for_update,
            nested_fields=nested_fields,
            # rev6 #10: capture a stable fingerprint of the schema-hook field shape NOW (class
            # validation) so the phase-2.5 bind can detect a nondeterministic hook that drifted.
            # rev6 #17 review P1: fingerprint the EFFECTIVE (writable + narrowed) set - the SAME
            # set the input build uses - so a read-only / narrowed-away nested serializer (whose
            # ``.fields`` need not even materialize no-arg) is never descended into. review P2:
            # gate the recursion on ``nested_fields`` so an UNOPTED nested field is not descended
            # into either (the field walk raises the canonical opt-in error instead).
            schema_fingerprint=serializer_schema_fingerprint(
                effective,
                nested_configs=nested_fields,
            ),
        )

    @classmethod
    def get_serializer_for_schema(cls) -> dict[str, serializers.Field]:
        """Return the serializer's SCHEMA-TIME field map (the overridable Decision-7 hook).

        The input is generated at finalization - BEFORE any request exists - so the
        DEFAULT discovers the field set by constructing ``serializer_class()`` with no
        args and reading its (lazily-built) ``.fields`` (delegating to the module-level
        ``rest_framework/inputs.py`` discovery, which wraps the ``.fields``
        materialization in the loud-rejection guard). A serializer whose ``.fields``
        cannot be materialized no-arg - a constructor-kwarg-requiring serializer, or a
        ``get_fields()`` that reads ``self.context`` - **overrides this classmethod** to
        return a stable, request-INDEPENDENT field map (spec-039 Decision 7 /
        Critical-2). This is the public escape hatch; the runtime
        ``get_serializer_kwargs`` seam is distinct (it shapes the per-request serializer
        and cannot substitute for schema-time discovery).

        Consulted at class-creation validation AND at the phase-2.5 ``build_input`` bind;
        never on the query path (the Slice-3 decode reads the bind-stashed reverse map).
        The default reads the serializer from the mutation's OWN validated snapshot when
        present (the bind window) else from ``cls.Meta.serializer_class`` (class creation,
        before the snapshot is assigned), resolving the SAME serializer in both windows.

        The snapshot is read via ``cls.__dict__`` - the OWN snapshot only, NOT an
        inherited one (spec-039 Medium): the metaclass assigns ``_mutation_meta`` AFTER
        ``_validate_meta`` runs, so during a SUBCLASS's validation ``cls._mutation_meta``
        would resolve up the MRO to the PARENT's snapshot (the parent's serializer),
        making the default hook discover the wrong serializer's fields. Reading
        ``cls.__dict__.get("_mutation_meta")`` returns ``None`` until the class's own
        snapshot is assigned, so a subclass redefining ``Meta.serializer_class`` validates
        against ``cls.Meta.serializer_class`` (its OWN ``Meta``), not the parent's.
        """
        meta = cls.__dict__.get("_mutation_meta")
        serializer_class = meta.serializer_class if meta is not None else cls.Meta.serializer_class
        return _default_serializer_schema_fields(serializer_class)

    @classmethod
    def build_input(cls, meta: _ValidatedMutationMeta, primary_type: type) -> type | None:
        """Build + materialize the operation's serializer-derived input (the seam override).

        Mirrors the ``038`` form flavor's one-input-per-operation shape: a ``create``
        materializes the ``CREATE``-shaped ``<Serializer>Input``, an ``update``
        materializes the ``PARTIAL``-shaped ``<Serializer>PartialInput``. The schema-time
        field set comes from the OVERRIDABLE ``get_serializer_for_schema()`` classmethod
        hook (spec-039 Critical-2), consulted ONCE here and threaded into the Slice-1
        generator so the bind honors a consumer override (a context-requiring serializer)
        rather than re-discovering through the module default. ``Meta.optional_fields``
        (the mutation's key - Critical-1) is threaded from the snapshot so the create
        input's requiredness + the descriptor identity reflect it.

        The per-shape build cache is keyed on the FULL ``SerializerInputShape``
        descriptor (spec-039 Critical-2), NOT a pre-build ``(class, op, names)`` tuple:
        two declarations on the same serializer + effective names but different
        hook-returned field specs or ``optional_fields`` produce DISTINCT descriptors, so
        neither reuses the other's stale cached class; identical descriptors reuse ONE
        class object so ``materialize_serializer_input_class`` dedupes idempotently
        (rather than two same-named classes colliding). The shape is therefore BUILT (a
        pure, finalization-time walk) before the dedupe; the build is idempotent (the
        read DjangoType's choice enums are cached per (model, field)), so building a shape
        that then dedupes is harmless.

        **P1.7 reuse is partial here, by necessity.** This seam rides the promoted
        ``build_and_stash_input`` (the materialize-then-stash-``_input_field_specs`` tail,
        shared with the form flavor) but does NOT route the cache lookup through
        ``cached_build_input``: that helper looks up its key BEFORE building, which the
        form flavor can do because its key (``form_class``, operation, effective names) is
        known pre-build, whereas the serializer's key is the ``SerializerInputShape``
        DESCRIPTOR - only knowable AFTER the build's pure walk produces it. Forcing this
        path through ``cached_build_input`` would mean building the shape TWICE (once to
        derive the key, once inside ``build_fn`` on a miss), the exact waste P1.7 names; so
        the descriptor-keyed dedupe stays an inline lookup-or-store, keyed on the post-build
        descriptor, while the guard-before-dedupe ordering is preserved here directly. The
        per-declaration guard discipline ``cached_build_input`` single-sites is upheld below
        (the create-required guard runs in ``_build`` per declaration, before the dedupe).

        The create-required-narrowing guard (``guard_create_required_serializer_fields``)
        runs PER declaration, BEFORE the descriptor dedupe, and is WAIVED when the
        concrete mutation overrides ``get_serializer_kwargs`` (spec-039 Slice 2 waiver via
        the promoted ``_hook_overridden``): the override injects whatever fields a
        narrowing dropped, so the guard trusts it. The Slice-1 reverse-map ``field_specs``
        are stashed on the mutation (``cls._input_field_specs``) for the Slice-3 decode.
        """
        del (
            primary_type
        )  # the serializer input derives from the serializer, not the model primary.
        operation_kind = NON_DELETE_OPERATION_INPUT_KIND[meta.operation]
        serializer_class = meta.serializer_class
        # rev6 #10 / rev2 P2: read the schema hook through the ONE guarded path, so the
        # determinism fingerprint is checked HERE and in ``input_type_name`` alike (no unguarded
        # second read). Then stash the schema-time specs for ``Meta.injected_fields`` (rev2 P1)
        # so the resolver can hold each injected field to the runtime-agreement contract.
        field_map = _checked_schema_field_map(cls, meta)
        cls._injected_field_specs = resolve_injected_field_specs(
            serializer_class,
            field_map,
            meta.injected_fields,
        )
        effective_names = tuple(
            resolve_effective_serializer_fields(
                serializer_class,
                fields=meta.fields,
                exclude=meta.exclude,
                field_map=field_map,
            ),
        )
        # The create-required guard (spec-039 rev6 #2). ``Meta.injected_fields`` is the
        # SANCTIONED, auditable path: when declared, the guard RUNS but subtracts those fields
        # (a dropped required field NOT declared injected still raises), and the resolver
        # verifies they reach the serializer's data. The old blanket
        # ``get_serializer_kwargs``-override waiver survives ONLY as an explicitly-named unsafe
        # legacy escape hatch - it fully skips the guard, but ONLY when ``injected_fields`` is
        # NOT declared (declaring ``injected_fields`` opts into the precise mechanism). The
        # partial (update) shape is never create-required guarded (all fields optional).
        legacy_waiver = (
            _hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")
            and not meta.injected_fields
        )

        def _build() -> tuple[type, Any]:
            # The create-required guard runs PER DECLARATION, BEFORE the per-shape
            # descriptor dedupe (the descriptor cache key excludes the waiver / injection
            # state), so a waiving mutation that materializes a narrowed shape FIRST cannot
            # suppress the guard for a later non-waiving mutation reusing the same cached shape.
            if operation_kind == CREATE and not legacy_waiver:
                guard_create_required_serializer_fields(
                    serializer_class,
                    effective_names,
                    injected_fields=meta.injected_fields,
                    field_map=field_map,
                )
            return _serializer_input_shape_for(
                meta,
                operation_kind=operation_kind,
                field_map=field_map,
            )

        input_cls = build_and_stash_input(
            cls,
            build=_build,
            materialize=materialize_serializer_input_class,
            specs_of=lambda shape: list(shape.field_specs),
        )
        cls._input_type_name = input_cls.__name__
        return input_cls

    @classmethod
    def input_type_name(cls, meta: _ValidatedMutationMeta) -> str:
        """Return the generated serializer-input class name (the name seam override).

        The serializer-flavor name single-sourced with ``build_input``'s name choice:
        before bind it resolves the Slice-1 descriptor through
        ``_serializer_input_shape_for``; after bind it reads the materialized name
        stashed by ``build_input``. The Slice-1 generator owns the name derivation;
        there is no second name deriver here (the descriptor carries
        ``type_name``), so the bind's materialized name and the field-factory's
        ``data:`` ref cannot drift.
        """
        operation_kind = NON_DELETE_OPERATION_INPUT_KIND[meta.operation]
        # rev2 P2: the SAME guarded hook read as ``build_input`` (fingerprint-checked), so
        # the type-name derivation never reads an unguarded field map. Run this even
        # when the bound name is already stashed; explicit calls to this seam still
        # enforce the determinism contract.
        field_map = _checked_schema_field_map(cls, meta)
        bound_name = cls.__dict__.get("_input_type_name")
        if bound_name is not None:
            return bound_name
        _input_cls, shape = _serializer_input_shape_for(
            meta,
            operation_kind=operation_kind,
            field_map=field_map,
        )
        return shape.type_name

    def get_serializer_kwargs(
        self,
        info: Any,
        *,
        data: Any,
        instance: Any = None,
    ) -> dict[str, Any]:
        """The default serializer-construction kwargs (the Slice-3 resolver consumes this).

        The graphene ``get_serializer_kwargs`` parity seam (spec-039 Decision 7 step 4 /
        Decision 8). The default returns ``{"data": data}`` (create) or ``{"data": data,
        "instance": instance}`` (update, when ``instance`` is non-``None``). A consumer
        overrides this to add / replace CONSTRUCTOR kwargs (an extra ``context`` key, a
        constructor argument like ``tenant``), or to inject a narrowed-away required field's
        VALUE into ``data``.

        **Narrowing away a required field: use ``Meta.injected_fields`` (rev6 #2).** The
        auditable, per-field contract is ``Meta.injected_fields`` - it names the fields this
        override supplies, so the create-required guard subtracts ONLY those (a dropped required
        field NOT declared injected still fails loud), and the resolver verifies at runtime that
        each declared injected field reached the data AND agrees with the runtime serializer
        (present / writable / source / kind / relation-model). The OLD "overriding this hook
        waives ALL required-field coverage" behavior survives ONLY as an explicitly-named
        UNSAFE legacy escape hatch in ``build_input`` (``legacy_waiver``): it fully skips the
        guard, but ONLY when ``Meta.injected_fields`` is not declared. Prefer
        ``Meta.injected_fields``.

        **The non-overridable framework invariants are NOT set here.** The Slice-3
        resolver's ``_merged_serializer_kwargs`` merges this return UNDER ``partial=True``
        (update only) and ``context["request"]`` (the framework request - the actor the
        inherited ``check_permission`` seam authorized against), spec-039 H3, so those
        invariants never live in the consumer-overridable hook (a hook returning
        ``partial`` itself, or a DIFFERENT ``context["request"]`` object, is a
        ``ConfigurationError`` there). This default never sets ``partial`` or
        ``context`` - the framework owns both - and ``build_input``'s legacy-waiver check
        (``_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")``) compares
        against it (the ``forms/sets.py`` ``get_form_kwargs`` precedent).
        """
        del info  # the default ignores ``info``; an override may consult it.
        # The "add ``instance`` only on update" clause is single-sited in
        # ``mutations/sets.py::construction_kwargs`` (spec-039 Md7), shared with the
        # form ``get_form_kwargs`` default.
        return construction_kwargs(data=data, instance=instance)

    def get_serializer_save_kwargs(
        self,
        info: Any,
        data: Any,
        instance: Any = None,
    ) -> dict[str, Any]:
        """Return extra kwargs for ``serializer.save(**kwargs)`` (spec-039 rev6 #12).

        The DRF-native customization point for request-derived data DRF expects at SAVE time
        (``serializer.save(owner=request.user)``) rather than in the constructor or by mutating
        ``data`` - distinct from ``get_serializer_kwargs`` (which shapes CONSTRUCTION / context).
        The default returns ``{}``; a consumer overrides it to inject save-time attributes. The
        Slice-3 resolver calls it inside the value-preserving ``save()`` closure (so the
        transaction / error-mapping / optimizer re-fetch behavior is preserved) and REJECTS a
        save kwarg that shadows a serializer input field (it would silently override the client's
        input). ``data`` is the decoded ``provided_data``; ``instance`` is the located row on
        update (``None`` on create).
        """
        del info, data, instance  # the default injects nothing; an override may consult them.
        return {}

    # The sync / async serializer resolver seams (delegate to the Slice-3 serializer
    # pipeline: locate -> authorize -> decode -> construct -> validate -> save ->
    # optimizer re-fetch -> payload, riding the promoted shared write skeleton), via
    # the shared ``resolver_seams`` factory (spec-039 M1b). The generated seams'
    # function-local import of ``rest_framework/resolvers.py`` keeps this module free
    # of a load-time edge to the resolver module (the ``forms/sets.py`` precedent).
    resolve_sync, resolve_async = resolver_seams(
        "django_strawberry_framework.rest_framework.resolvers",
        "resolve_serializer_sync",
        "resolve_serializer_async",
    )
