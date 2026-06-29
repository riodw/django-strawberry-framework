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

from typing import Any

from rest_framework import serializers

from ..exceptions import ConfigurationError
from ..mutations.inputs import CREATE, PARTIAL
from ..mutations.sets import (
    NON_DELETE_WRITE_OPERATIONS,
    DjangoMutation,
    _hook_overridden,
    _ValidatedMutationMeta,
    build_and_stash_input,
    non_delete_operation_error,
    reject_unknown_meta_keys,
)
from ..mutations.sets import (
    _validate_permission_classes as _validate_mutation_permission_classes,
)
from .inputs import (
    SERIALIZER_INPUTS_MODULE_PATH,
    _serializer_shape_build_cache,
    build_serializer_input_class,
    guard_create_required_serializer_fields,
    materialize_serializer_input_class,
    normalize_serializer_field_sequence,
    resolve_effective_serializer_fields,
    resolve_optional_fields,
)
from .inputs import (
    get_serializer_for_schema as _default_serializer_schema_fields,
)

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
        "operation",
        "fields",
        "exclude",
        "permission_classes",
    },
)

# ``operation`` -> input-generator kind. ``create`` builds the required-aware
# ``<Serializer>Input`` (``CREATE``); ``update`` builds the all-optional
# ``<Serializer>PartialInput`` (``PARTIAL``). Single-sourced so ``build_input`` and
# ``input_type_name`` cannot drift on the mapping (the ``036`` / ``038``
# operation->kind map precedent).
_SERIALIZER_OPERATION_INPUT_KIND: dict[str, str] = {"create": CREATE, "update": PARTIAL}


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
        serializer_class = getattr(meta, "serializer_class", None)
        serializer_meta = getattr(serializer_class, "Meta", None)
        return getattr(serializer_meta, "model", None)

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
          ``resolve_effective_serializer_fields``, which routes through
          ``normalize_field_name_sequence(flavor="SerializerMutation")`` directly
          (P2.7 - no new wrapper).

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

        serializer_class = getattr(meta, "serializer_class", None)
        if serializer_class is None:
            raise ConfigurationError(
                f"SerializerMutation {name}.Meta declares no serializer_class; set "
                "Meta.serializer_class to a serializers.ModelSerializer subclass.",
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

        model = cls._resolve_model(meta)
        if model is None:
            raise ConfigurationError(
                f"SerializerMutation {name}.Meta.serializer_class {serializer_class.__name__} "
                "resolves no model; a ModelSerializer must set Meta.model so the mutation has a "
                "model + a DjangoType to return.",
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
        # empty-set guard), which routes through
        # ``normalize_serializer_field_sequence`` ->
        # ``normalize_field_name_sequence(flavor="SerializerMutation")`` (P2.7 - the
        # serializer flavor's single field-sequence entry, not a new wrapper). The
        # snapshot stores the RAW declarations; ``build_input`` re-resolves them (D1
        # - the form flavor's validate-then-store-raw precedent).
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
        optional_fields = normalize_serializer_field_sequence(
            getattr(meta, "optional_fields", None),
            label="optional_fields",
        )
        resolve_optional_fields(serializer_class, optional_fields, tuple(effective))

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
        operation_kind = _SERIALIZER_OPERATION_INPUT_KIND[meta.operation]
        serializer_class = meta.serializer_class
        field_map = cls.get_serializer_for_schema()
        effective_names = tuple(
            resolve_effective_serializer_fields(
                serializer_class,
                fields=meta.fields,
                exclude=meta.exclude,
                field_map=field_map,
            ),
        )
        # Waive the create-required guard when the concrete mutation overrides the
        # serializer-construction hook (it injects whatever a narrowing dropped). The
        # partial (update) shape is never create-required guarded (it widens every
        # field optional), so only the create path runs the guard.
        guard_waived = _hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")

        def _build() -> tuple[type, Any]:
            # The create-required guard runs PER DECLARATION, BEFORE the per-shape
            # descriptor dedupe (the descriptor cache key excludes the waiver flag), so
            # a waiving mutation that materializes a narrowed shape FIRST cannot suppress
            # the guard for a later non-waiving mutation reusing the same cached shape.
            if operation_kind == CREATE and not guard_waived:
                guard_create_required_serializer_fields(
                    serializer_class,
                    effective_names,
                    field_map=field_map,
                )
            input_cls, shape = build_serializer_input_class(
                serializer_class,
                operation_kind=operation_kind,
                fields=meta.fields,
                exclude=meta.exclude,
                optional_fields=meta.optional_fields,
                field_map=field_map,
            )
            # Dedupe on the full descriptor: identical shapes reuse one class object
            # (the materialize ledger then dedupes idempotently); distinct shapes keep
            # their own classes + descriptor-derived names.
            cached = _serializer_shape_build_cache.get(shape.cache_key)
            if cached is not None:
                return cached
            _serializer_shape_build_cache[shape.cache_key] = (input_cls, shape)
            return input_cls, shape

        return build_and_stash_input(
            cls,
            build=_build,
            materialize=materialize_serializer_input_class,
            specs_of=lambda shape: list(shape.field_specs),
        )

    @classmethod
    def input_type_name(cls, meta: _ValidatedMutationMeta) -> str:
        """Return the generated serializer-input class name (the name seam override).

        The serializer-flavor name single-sourced with ``build_input``'s name choice:
        re-build the shape via the Slice-1 ``build_serializer_input_class`` and read
        ``shape.type_name`` (the ``<Serializer>Input`` / ``<Serializer>PartialInput``
        canonical name, or a descriptor-derived name for a divergent shape). The
        Slice-1 generator owns the name derivation; there is no second name deriver
        here (the descriptor carries ``type_name``), so the bind's materialized name
        and the field-factory's ``data:`` ref cannot drift.
        """
        operation_kind = _SERIALIZER_OPERATION_INPUT_KIND[meta.operation]
        _input_cls, shape = build_serializer_input_class(
            meta.serializer_class,
            operation_kind=operation_kind,
            fields=meta.fields,
            exclude=meta.exclude,
            optional_fields=meta.optional_fields,
            field_map=cls.get_serializer_for_schema(),
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
        overrides this to add / replace kwargs (an extra ``context`` key, an extra
        constructor kwarg), which WAIVES ``build_input``'s create-required guard (the
        override injects whatever a narrowing dropped).

        **The non-overridable framework invariants are NOT set here.** The Slice-3
        resolver's ``_merged_serializer_kwargs`` merges this return UNDER ``partial=True``
        (update only) and ``context["request"]`` (the framework request - the actor the
        inherited ``check_permission`` seam authorized against), spec-039 H3, so those
        invariants never live in the consumer-overridable hook (a hook returning
        ``partial`` itself, or a DIFFERENT ``context["request"]`` object, is a
        ``ConfigurationError`` there). This default never sets ``partial`` or
        ``context`` - the framework owns both - and ``build_input``'s
        ``_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")`` waiver
        compares against it (the ``forms/sets.py`` ``get_form_kwargs`` precedent).
        """
        del info  # the default ignores ``info``; an override may consult it.
        kwargs: dict[str, Any] = {"data": data}
        if instance is not None:
            kwargs["instance"] = instance
        return kwargs

    @classmethod
    def resolve_sync(
        cls,
        info: Any,
        *,
        data: Any,
        id: Any,  # noqa: A002  # ``id`` is the GraphQL arg name
    ) -> Any:
        """The sync serializer resolver seam (delegates to the Slice-3 serializer pipeline).

        The D8 carry-forward from Slice 2 (which left ``SerializerMutation`` without
        the overrides because ``rest_framework/resolvers.py`` did not exist yet -
        an inert declaration inherited ``DjangoMutation``'s callable pair). Routes to
        ``rest_framework/resolvers.py::resolve_serializer_sync`` (the
        locate -> authorize -> decode -> construct -> validate -> save -> optimizer
        re-fetch -> payload pipeline, riding the promoted shared write skeleton). The
        import is local to keep ``rest_framework/sets.py`` free of a load-time edge
        to the resolver module (the ``forms/sets.py`` precedent).
        """
        from .resolvers import resolve_serializer_sync

        return resolve_serializer_sync(cls, info, data=data, id=id)

    @classmethod
    def resolve_async(
        cls,
        info: Any,
        *,
        data: Any,
        id: Any,  # noqa: A002  # ``id`` is the GraphQL arg name
    ) -> Any:
        """The async serializer resolver seam (delegates to the Slice-3 serializer pipeline).

        Routes to ``rest_framework/resolvers.py::resolve_serializer_async`` (the sync
        body in one ``sync_to_async(thread_sensitive=True)`` call via the shared
        ``run_pipeline_async`` boundary).
        """
        from .resolvers import resolve_serializer_async

        return resolve_serializer_async(cls, info, data=data, id=id)
