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
``forms/sets.py``). The default ``get_serializer_kwargs`` / ``get_serializer``
construction hooks ship here so ``build_input``'s ``_hook_overridden`` waiver has a
base to compare against (the ``forms/sets.py`` ``get_form_kwargs`` / ``get_form``
precedent); the Slice-3 resolver consumes ``get_serializer_kwargs`` (the finer hook
the spec D8 step 4 names) and OWNS the framework merge / ``partial`` injection / H3
``ConfigurationError`` rules on top of its return, so those framework-owned
invariants never live in the consumer-overridable hook.
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
    cached_build_input,
    non_delete_operation_error,
    reject_unknown_meta_keys,
)
from ..mutations.sets import (
    _validate_permission_classes as _validate_mutation_permission_classes,
)
from ..utils.permissions import request_from_info
from .inputs import (
    SERIALIZER_INPUTS_MODULE_PATH,
    _serializer_shape_build_cache,
    build_serializer_input_class,
    guard_create_required_serializer_fields,
    materialize_serializer_input_class,
    resolve_effective_serializer_fields,
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
        re-read off the serializer's own ``Meta`` by the generator, so it is NOT a
        snapshot slot (D2); its bare-string / unknown-name rejection runs at bind via
        ``build_serializer_input_class`` -> ``resolve_optional_fields``.
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
        # Validate the narrowing fail-loud via the Slice-1 machinery (mutual
        # exclusion, bare-string incl. ``"__all__"`` / duplicate / unknown-name /
        # empty-set guard), which routes through
        # ``normalize_serializer_field_sequence`` ->
        # ``normalize_field_name_sequence(flavor="SerializerMutation")`` (P2.7 - the
        # serializer flavor's single field-sequence entry, not a new wrapper). The
        # snapshot stores the RAW declarations; ``build_input`` re-resolves them (D1
        # - the form flavor's validate-then-store-raw precedent).
        resolve_effective_serializer_fields(serializer_class, fields=fields, exclude=exclude)

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
        )

    @classmethod
    def build_input(cls, meta: _ValidatedMutationMeta, primary_type: type) -> type | None:
        """Build + materialize the operation's serializer-derived input (the seam override).

        Mirrors the ``038`` form flavor's one-input-per-operation shape: a ``create``
        materializes the ``CREATE``-shaped ``<Serializer>Input``, an ``update``
        materializes the ``PARTIAL``-shaped ``<Serializer>PartialInput``. The input
        comes from the Slice-1 generator (the serializer's schema-time field set, the
        symmetric model-backed converters), materialized into ``rest_framework.inputs``
        via ``materialize_serializer_input_class`` so the lazy ``data:`` ref resolves
        there.

        Rides the PROMOTED ``cached_build_input`` (guard-before-cache-lookup, keyed on
        a pre-build shape identity) + ``build_and_stash_input`` (materialize-then-stash
        the reverse-map ``field_specs``) - NOT a byte-parallel serializer-local
        cache/build trio. The create-required-narrowing guard
        (``guard_create_required_serializer_fields``) runs PER declaration, BEFORE the
        per-shape cache lookup, and is WAIVED when the concrete mutation overrides
        ``get_serializer_kwargs`` (spec-039 Slice 2 waiver via the promoted
        ``_hook_overridden``): the override injects whatever fields a narrowing
        dropped, so the guard trusts it. The Slice-1 reverse-map ``field_specs`` are
        stashed on the mutation (``cls._input_field_specs``) for the Slice-3 decode.
        """
        del (
            primary_type
        )  # the serializer input derives from the serializer, not the model primary.
        operation_kind = _SERIALIZER_OPERATION_INPUT_KIND[meta.operation]
        serializer_class = meta.serializer_class
        effective_names = tuple(
            resolve_effective_serializer_fields(
                serializer_class,
                fields=meta.fields,
                exclude=meta.exclude,
            ),
        )
        # Waive the create-required guard when the concrete mutation overrides the
        # serializer-construction hook (it injects whatever a narrowing dropped). The
        # partial (update) shape is never create-required guarded (it widens every
        # field optional), so only the create path runs the guard.
        guard_waived = _hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")

        def _guard() -> None:
            if operation_kind == CREATE and not guard_waived:
                guard_create_required_serializer_fields(serializer_class, effective_names)

        def _build() -> tuple[type, Any]:
            return build_serializer_input_class(
                serializer_class,
                operation_kind=operation_kind,
                fields=meta.fields,
                exclude=meta.exclude,
            )

        # The per-shape cache key. The ``SerializerInputShape`` descriptor (the
        # Slice-1 cache key) is only known AFTER the build, so the cache lookup keys
        # on a cheap pre-build identity tuple that is deterministic in
        # ``(serializer_class, operation_kind, effective set)`` for a given
        # declaration - two declarations resolving the same shape share the key and
        # dedupe to one class object (the materialize ledger then dedupes
        # idempotently). ``cached_build_input`` returns ``(input_cls, shape)``;
        # ``build_and_stash_input`` extracts ``shape.field_specs`` as the stash value.
        shape_key = (serializer_class, operation_kind, frozenset(effective_names))

        return build_and_stash_input(
            cls,
            build=lambda: cached_build_input(
                _serializer_shape_build_cache,
                shape_key,
                guard=_guard,
                build_fn=_build,
            ),
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

        The graphene ``get_serializer_kwargs`` parity seam (spec-039 Decision 7 step
        4). The default returns ``{"data": data}`` (create) or ``{"data": data,
        "instance": instance}`` (update, when ``instance`` is non-``None``), plus
        ``"context": {"request": request_from_info(info)}`` so the serializer's own
        request-aware validators / ``HiddenField(default=CurrentUserDefault())``
        resolve. A consumer overrides this to add / replace kwargs (extra ``context``
        keys, an extra constructor kwarg), which WAIVES ``build_input``'s
        create-required guard (the override injects whatever a narrowing dropped).

        **Defined here; the framework-merge + ``partial`` injection that wrap it are
        Slice 3.** Slice 2 ships the default method body so ``build_input``'s
        ``_hook_overridden(cls, SerializerMutation, "get_serializer_kwargs")`` waiver
        has a base to compare against (the ``forms/sets.py`` ``get_form_kwargs``
        precedent). The Slice-3 resolver merges this return over its non-overridable
        ``partial`` / ``context["request"]`` rules (spec-039 H3); this default never
        sets ``partial`` (the framework owns it).
        """
        del info  # the default ignores ``info`` for kwargs other than the request context.
        kwargs: dict[str, Any] = {"data": data}
        if instance is not None:
            kwargs["instance"] = instance
        return kwargs

    def get_serializer(
        self,
        info: Any,
        *,
        data: Any,
        instance: Any = None,
    ) -> Any:
        """Construct the serializer from ``get_serializer_kwargs`` (the Slice-3 resolver consumes this).

        The coarser construction hook:
        ``serializer_class(**self.get_serializer_kwargs(...))`` plus the framework
        request ``context``. A consumer overrides this when it needs full control of
        instantiation; the finer ``get_serializer_kwargs`` override suffices for the
        common "inject a kwarg" case.

        **Defined here; the ``partial`` injection / framework-merge are Slice 3.**
        Like ``get_serializer_kwargs``, Slice 2 ships the default body as the waiver
        base; the Slice-3 resolver routes serializer construction through this hook
        after applying its non-overridable ``partial`` / ``context["request"]`` rules
        (spec-039 H3 - the request is the framework's, the same actor the inherited
        ``check_permission`` seam authorized against).
        """
        serializer_class = type(self)._mutation_meta.serializer_class
        kwargs = self.get_serializer_kwargs(info, data=data, instance=instance)
        context = dict(kwargs.get("context") or {})
        context["request"] = request_from_info(info, family_label="SerializerMutation")
        kwargs["context"] = context
        return serializer_class(**kwargs)

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
